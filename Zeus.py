import multiprocessing
import threading
import subprocess
import socket
import time
import logging, logging.config
import pdb
from LCP import lcp_provider
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


def thread_dispatch_rcp(my_pipe):
    logger = logging.getLogger('ZEUS_RCP')
    while True:
        the_query = my_pipe.recv()
        try:
            name, rest = the_query.split("|", 1)
        except Exception:
            my_pipe.send(b'bad format')
            continue

        if name not in name_lock_sockets:
            my_pipe.send(b'Dummy not found')
            continue

        lock = name_lock_sockets[name][0]
        with lock:
            s = name_lock_sockets[name][1]
            s.sendall(bytes(rest, 'ascii'))
            response = s.recv(256)
        my_pipe.send(response)

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
                s.sendall(b'version')
                dummy_version = s.recv(32)
                logger.debug('%s -- id:%s   version%s', name, dummy_id, dummy_version)
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
    rcp_pipe, other_side_pipe = multiprocessing.Pipe()
    rcp = multiprocessing.Process(name='rcp', target=lcp_provider.run,
                                  args=['Zeus', other_side_pipe], daemon=True)
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[rcp_pipe], daemon=True)
    rcp_thread.start()
    rcp.start()


    input("Press enter to kill them all")


    logger.info('Shutting down dummies')
    for dummy, port in dummy_processes.values():
        dummy.terminate()
        logger.debug('Dummy on port %s exited with %s return code', port, dummy.wait())
