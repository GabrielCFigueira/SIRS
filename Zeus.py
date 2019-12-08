import multiprocessing
import threading
import subprocess
import socket
import time
import logging, logging.config
import pdb
from UP import up_client

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ZEUS')


my_dummies = {5001: ['python3', 'Dummies/oil.py'],
              5002: ['python3', 'Dummies/gas.py'],
              5003: ['python3', 'Dummies/speed.py'],
              5011: ['python3', 'Dummies/brakes.py']}

# name -> (subprocess, port) GLOBAL UNLOCKED
dummy_processes = {}

# name -> (lock, shared socket) GLOBAL locked name by name
name_lock_sockets = {}


UPDATE_SLEEP = 3000
RETRY_FAILURES = 5
RETRY_SLEEP = 0.2

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


def thread_dummy_update():
    logger = logging.getLogger('ZEUS_UP')
    while True:
        logger.info('Checking for updates')
        num = 0
        for name, (lock, s) in name_lock_sockets.items():
            with lock:
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
                                           logger=logger)
                logger.debug('Return value: %s', res)
                if res[1] == True: # There was an update
                    logger.info('Dummy "%s" needs to be restarted', name)
                    num += 1
                    start_dummy(my_dummies[port], port)
        logger.info('Updated %s dummies', num)
        time.sleep(UPDATE_SLEEP)

if __name__ == '__main__':

    #global dummy_processes, name_lock_sockets
    #global logger

    # Launch Dummies
    logger.info('Start launching %s dummies', len(my_dummies))
    logger.debug('Dummies dict: %s', my_dummies)
    for port, cmd in my_dummies.items():
        start_dummy(cmd, port)


    # UP
    logger.info('Starting Update Protocol thread')
    up = threading.Thread(target=thread_dummy_update, args=[], daemon=True)
    up.start()


    # RCP #todo refactorize this to use the thread for everything?
    logger.info('Starting Remote Control Protocol thread')
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[], daemon=True)
    rcp_thread.start()


    input("Press enter to kill them all")


    logger.info('Shutting down dummies')
    for dummy, port in dummy_processes.values():
        dummy.terminate()
        logger.debug('Dummy on port %s exited with %s return code', port, dummy.wait())
