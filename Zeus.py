import multiprocessing
import threading
import subprocess
import socket
from LCP import lcp_provider

my_dummies = {5001: ['python3', 'Dummies/oil.py'],
             5002: ['python3', 'Dummies/gas.py'],
             5003: ['python3', 'Dummies/speed.py'],
             5011: ['python3', 'Dummies/brakes.py']}

#my_dummies = {0: ['python3', 'Dummies/GenericDummy.py']}


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

    print(dummies_lock_sockets)
    # RCP #todo refactorize this to use the thread for everything?
    rcp_pipe, other_side_pipe = multiprocessing.Pipe()
    rcp = multiprocessing.Process(name='rcp', target=lcp_provider.run,
                                  args=['Zeus', other_side_pipe], daemon=True)
    rcp_thread = threading.Thread(target=thread_dispatch_rcp, args=[dummies_lock_sockets, rcp_pipe], daemon=True)
    rcp_thread.start()
    rcp.start()

    input("Press enter to kill them all")

    for dummy in dummies.values():
        dummy.terminate()
        print(dummy.wait())
