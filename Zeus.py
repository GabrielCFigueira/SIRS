import multiprocessing
import threading
import subprocess
import socket
import time
from LCP import lcp_provider
from UP import up_client

my_dummies = {5001: ['python3', 'Dummies/oil.py'],
             5002: ['python3', 'Dummies/gas.py'],
             5003: ['python3', 'Dummies/speed.py'],
             5011: ['python3', 'Dummies/brakes.py']}

#my_dummies = {0: ['python3', 'Dummies/GenericDummy.py']}

UPDATE_SLEEP=3000

def thread_dispatch_rcp(name_lock_sockets, my_pipe):
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

def thread_dummy_update(name_lock_sockets):
    import pdb
    while True:
        for name, (lock, s) in name_lock_sockets.items():
            with lock:
                print("Updating {}".format(name))
                #pdb.set_trace()
                s.sendall(b'id')
                dummy_id = s.recv(10)
                s.sendall(b'version')
                dummy_version = s.recv(32)
                file_name = 'Dummies/{}.py'.format(name)
                res = up_client.try_update(dummy_id,
                                           dummy_version,
                                           file_name)
                print("Final result: {}".format(res))
        time.sleep(UPDATE_SLEEP)

if __name__ == '__main__':

    dummies = {}

    # Launch Dummies
    for port, cmd in my_dummies.items():
        # TODO: try to use integers for stdout/stderr
        dummies[port] = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)

    dummies_lock_sockets = {}
    # Get association between sockets and names
    input("Press enter to continue: ")
    for port in my_dummies.keys():
        print(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', port))
        s.sendall(b'name')
        name = str(s.recv(10), 'ascii')
        dummies_lock_sockets[name] = (threading.Lock(), s)


    # UP
    up = threading.Thread(target=thread_dummy_update, args=[dummies_lock_sockets], daemon=True)
    up.start()


    # RCP #todo refactorize this to use the thread for everything?
    rcp_pipe, other_side_pipe = multiprocessing.Pipe()
    rcp = multiprocessing.Process(name='rcp', target=lcp_provider.run,
                                  args=['Zeus', other_side_pipe], daemon=True)
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[dummies_lock_sockets, rcp_pipe], daemon=True)
    rcp_thread.start()
    rcp.start()


    #time.sleep(5000)
    input("Press enter to kill them all")

    for dummy in dummies.values():
        dummy.terminate()
        print(dummy.wait())
