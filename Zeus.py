import multiprocessing
import threading
import subprocess
import socket
import time
import pdb
from LCP import lcp_provider
from UP import up_client

my_dummies = {5001: ['python3', 'Dummies/oil.py'],
              5002: ['python3', 'Dummies/gas.py'],
              5003: ['python3', 'Dummies/speed.py'],
              5011: ['python3', 'Dummies/brakes.py']}

# name -> (subprocess, port) GLOBAL UNLOCKED
dummy_processes = {}

# name -> (lock, shared socket) GLOBAL locked name by name
name_lock_sockets = {}


UPDATE_SLEEP=3000
RETRY_FAILURES = 5
RETRY_SLEEP = 0.2

def shutdown_dummy(s, dummy):
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

def start_dummy(command, port):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

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

#my_dummies = {0: ['python3', 'Dummies/GenericDummy.py']}


def thread_dispatch_rcp(my_pipe):
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

    while True:
        for name, (lock, s) in name_lock_sockets.items():
            with lock:
                print("Updating {}".format(name))
                #pdb.set_trace()
                s.sendall(b'id')
                dummy_id = s.recv(10)
                s.sendall(b'version')
                dummy_version = s.recv(32)
                file_name = 'Dummies/{}.py'.format(name) # not general
                proc, port = dummy_processes[name]
                res = up_client.try_update(dummy_id,
                                           dummy_version,
                                           file_name,
                                           lambda: shutdown_dummy(s,proc))
                print("Final result: {}".format(res))
                if res[1] == True: # There was an update
                    start_dummy(my_dummies[port], port)
        time.sleep(UPDATE_SLEEP)

if __name__ == '__main__':

    #global dummy_processes, name_lock_sockets

    # Launch Dummies
    for port, cmd in my_dummies.items():
        start_dummy(cmd, port)


    # UP
    up = threading.Thread(target=thread_dummy_update, args=[], daemon=True)
    up.start()


    # RCP #todo refactorize this to use the thread for everything?
    rcp_pipe, other_side_pipe = multiprocessing.Pipe()
    rcp = multiprocessing.Process(name='rcp', target=lcp_provider.run,
                                  args=['Zeus', other_side_pipe], daemon=True)
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[rcp_pipe], daemon=True)
    rcp_thread.start()
    rcp.start()


    input("Press enter to kill them all")


    for dummy, _port in dummy_processes.values():
        dummy.terminate()
        print(dummy.wait())
