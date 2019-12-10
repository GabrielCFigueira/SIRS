import multiprocessing
import threading
import subprocess
import socket
import time, datetime
import logging, logging.config
import pdb
#from UP import up_client
from CP import cp_utils

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ZEUS')


my_dummies = {5001: ['python3', 'Dummies/oil.py'],
              5002: ['python3', 'Dummies/gas.py'],
              5003: ['python3', 'Dummies/speed.py'],
              5011: ['python3', 'Dummies/brakes.py']}

# name -> (subprocess, port) GLOBAL UNLOCKED (só dummy update deve mexer)
dummy_processes = {}

# name -> (lock, shared socket) GLOBAL locked name by name
name_lock_sockets = {}

# shared lock to synchronize certificate updating and everybody else
# name -> (lock, shared cert) GLOBAL
cert_store = {'UP': [threading.Lock(), None]}

UPDATE_SLEEP = 30
MONOTORING_SLEEP = 30
RETRY_FAILURES = 5
RETRY_SLEEP = 0.2
CHUNK_SIZE = 4096


def shutdown_dummy(s, dummy, logger=logger):
    try:
        s.sendall(b'kill')
        r = s.recv(3)
        if r != b'ack':
            print("This is weird, should not happen")
        dummy.wait(timeout=5) #5 seconds
        return True
    except BrokenPipeError:
        pass #maybe was already dead
    except:
        return False

def start_dummy(command, port, logger=logger):
    #proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc = subprocess.Popen(cmd, stdout=1, stderr=2)

    attempts, success = 0, False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while attempts < RETRY_FAILURES and success == False:
        attempts += 1
        time.sleep(RETRY_SLEEP) # give time for setting up socket
        try:
            s.connect(('127.0.0.1', port))
            success = True
            break
        except ConnectionRefusedError:
            pass

    if not success:
        print("Unable to connect to program {} on port {}".format(command, port))
        return

    s.sendall(b'name')
    name = str(s.recv(10), 'ascii')
    name_lock_sockets[name] = (threading.Lock(), s)
    dummy_processes[name] = (proc, port)


def thread_dispatch_rcp():
    logger = logging.getLogger('ZEUS_RCP')
    logger.info('Waiting for commands')
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.debug('Trying to bind on port %s', 5679)
            s.bind(('', 5679))
            s.listen(1)
            logger.debug('Waiting for connection on %s', s.getsockname())
            conn, addr = s.accept()
            logger.info('Received connection from %s', addr)
            try:
                while True:
                    the_query = conn.recv(16).decode('utf-8').strip()
                    logger.debug('Got "%s" on the pipe', the_query)
                    if the_query == 'quit':
                        break
                    try:
                        name, rest = the_query.split("|", 1)
                    except Exception:
                        conn.sendall(b'Bad format')
                        continue

                    if name not in name_lock_sockets:
                        conn.sendall(b'Dummy not found')
                        continue

                    lock = name_lock_sockets[name][0]
                    with lock:
                        s = name_lock_sockets[name][1]
                        s.sendall(bytes(rest, 'ascii'))
                        response = s.recv(256)

                    logger.debug('Responding with "%s"', response)
                    conn.sendall(response)
            except BrokenPipeError:
                logger.warning('%s disconnected without "quit"', addr)


def thread_what_mp():
    logger = logging.getLogger('ZEUS_MP')
    HOST, PORT = "localhost", 5555
    conn = socket.create_connection((HOST, PORT))
    while True:
        conn.sendall(b'zeus|what')
        response = conn.recv(16)
        print(response)
        time.sleep(MONOTORING_SLEEP)
    """
    logger = logging.getLogger('ZEUS_MP')
    HOST, PORT = "localhost", 5555
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            logger.info('Sending an MP what')
            s.sendall(b'zeus|what')
            time.sleep(MONOTORING_SLEEP)
    ""



            ""
                logger.debug('%s -- version: %s', name, dummy_version)
                file_name = 'Dummies/{}.py'.format(name) # FIXME: not general
                proc, port = dummy_processes[name]
                res = up_client.try_update(dummy_id,
                                           dummy_version,
                                           file_name,
                                           lambda: shutdown_dummy(s,proc),
                                           logger=logger)
                logger.debug('Return value: %s', res)
                if res[1] == True: # There was an update
                    logger.info('Dummy "%s" needs to be restarted', name)
                    num += 1
                    start_dummy(my_dummies[port], port)
    """
    logger.info('Sent what message to heimdall')
    time.sleep(MONOTORING_SLEEP)


def thread_dummy_update():
    logger = logging.getLogger('ZEUS_UP')
    while True:
        logger.info('Checking for updates')
        num = 0
        for name, (lock, s) in name_lock_sockets.items():
            cert_lock = cert_store['UP'][0]
            with cert_lock, lock:
                pubkey = cert_store['UP'][1]
                if not pubkey:
                    logger.warning('Cannot update while no UP certificates are known')
                    break
                else:
                    pubkey = pubkey.public_key()
                s = name_lock_sockets[name][1]
                logger.debug('Get id and version from %s', name)
                s.sendall(b'id')
                dummy_id = s.recv(10)
                logger.debug('%s -- id: %s', name, dummy_id)
                s.sendall(b'version')
                dummy_version = s.recv(32)
                logger.debug('%s -- version: %s', name, dummy_version)
                file_name = 'Dummies/{}.py'.format(name) # FIXME: not general
                proc, port = dummy_processes[name]
                res = up_client.try_update(dummy_id,
                                           dummy_version,
                                           file_name,
                                           lambda: shutdown_dummy(s,proc),
                                           pubkey,
                                           logger=logger)
                logger.debug('Return value: %s', res)
                if res[1] == True: # There was an update
                    logger.info('Dummy "%s" needs to be restarted', name)
                    num += 1
                    start_dummy(my_dummies[port], port)
        logger.info('Updated %s dummies', num)
        time.sleep(UPDATE_SLEEP)



def thread_certificate_checking():
    logger = logging.getLogger('ZEUS_CP')

    def get_pem_from_arch(what, filename, date_for_update=datetime.datetime.today()):

        if date_for_update < datetime.datetime.today():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Connect to server and send update version request
                #pdb.set_trace()
                try:
                    logger.debug('Getting new %s', what)
                    sock.connect(("127.1", 5900))
                    sock.sendall(bytes(what, 'utf-8'))
                    size = int.from_bytes(sock.recv(8), 'big')
                    with open(filename, 'wb') as outfile:
                        while size > 0:
                            chunk = sock.recv(CHUNK_SIZE if CHUNK_SIZE < size else size)
                            outfile.write(chunk)
                            size -= len(chunk)
                    logger.debug('Finished getting %s', what)
                except (ConnectionRefusedError, BrokenPipeError):
                    logger.warning('Unable to connect to Certificate Server in %s', 'architect')
        else:
            logger.debug('Not getting new %s', what)

        if what == 'CRL':
            crl = cp_utils.read_crl(filename)
            return crl
        else:
            cert = cp_utils.read_cert(filename)
            return cert



    up_cert = get_pem_from_arch('UP', 'zeus_current_up_cert.pem')
    crl_next_update = datetime.datetime.today()
    while True:
        cert_lock = cert_store['UP'][0]
        with cert_lock:
            crl = get_pem_from_arch('CRL', 'zeus_current_crl.pem', crl_next_update)
            while not cp_utils.check_certificate('zeus_current_up_cert.pem', 'root_cert.pem', 'zeus_current_crl.pem'):
                logger.warning('No valid UP certificate')
                time.sleep(5)
                up_cert = get_pem_from_arch('UP', 'zeus_current_up_cert.pem')
                crl = get_pem_from_arch('CRL', 'zeus_current_crl.pem', crl.next_update)
            logger.info('Got valid certificates')
            cert_store['UP'][1] = up_cert
            crl_next_update = crl.next_update


        nearest_datetime = crl.next_update if crl.next_update < up_cert.not_valid_after else up_cert.not_valid_after
        time.sleep(((nearest_datetime-datetime.datetime.today())/2).seconds)




if __name__ == '__main__':

    #global dummy_processes, name_lock_sockets
    #global logger

    # Launch Dummies
    logger.info('Start launching %s dummies', len(my_dummies))
    logger.debug('Dummies dict: %s', my_dummies)
    for port, cmd in my_dummies.items():
        start_dummy(cmd, port)


    # CP
    logger.info('Starting Certificate Protocol thread')
    cp = threading.Thread(target=thread_certificate_checking, args=[], daemon=True)
    cp.start()

    # UP
    """logger.info('Starting Update Protocol thread')
    up = threading.Thread(target=thread_dummy_update, args=[], daemon=True)
    up.start()"""


    # RCP #todo refactorize this to use the thread for everything?
    logger.info('Starting Remote Control Protocol thread')
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[], daemon=True)
    rcp_thread.start()

    # MP
    logger.info('Starting Monotoring Protocol thread')
    mp_thread = threading.Thread(target=thread_what_mp, args=[], daemon=True)
    mp_thread.start()


    #time.sleep(5000)
    input("Press enter to kill them all")


    logger.info('Shutting down dummies')
    for dummy, port in dummy_processes.values():
        dummy.terminate()
        logger.debug('Dummy on port %s exited with %s return code', port, dummy.wait())
