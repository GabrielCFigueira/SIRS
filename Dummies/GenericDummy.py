import time
import os
import signal
from multiprocessing import Process
import logging
import socket
import threading
import sys

logging.basicConfig(format='%(message)s', level=logging.INFO)


class GenericDummy(Process):
    def __init__(self):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        super(GenericDummy, self).__init__()
        self.interval = 2 # can be configured
        self.lock = threading.Lock()
        self.port = 5000
        self.state = self.update_state()
        self.sock = None

    def update_state(self):
        pass

    def set_state(self, _new):
        # only implement if you want to allow direct modification
        pass


    def get_state(self):
        with self.lock:
            return self.state

    def thread_update(self):
        while True:
            time.sleep(self.interval)
            with self.lock:
                new_state = self.update_state()
                print("Updating state from {} to {}".format(self.state, new_state))
                self.state = new_state

    def set_a_new_state_carefully(self, new):
        with self.lock:
            new_state = self.set_state(new)
            print("Changing state from {} to {}".format(self.state, new_state))
            self.state = new_state


    def run(self):
        state_updater = threading.Thread(target=self.thread_update, args=[],
                                         daemon=True)
        state_updater.start()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:

            self.sock.bind(('127.0.0.1', self.port))
            self.sock.listen(1)
            conn, _addr = self.sock.accept()
            with conn:
                while True:
                    query = conn.recv(16).decode('utf-8').rstrip().split('|')
                    if query[0] == 'read':
                        conn.sendall(bytes(self.get_state(), 'ascii'))
                    elif query[0] == 'kill':
                        sys.exit(0)
                    elif query[0] == 'set':
                        self.set_a_new_state_carefully(query[1])

def start_the_dummy(DummyClass):

    def forward_signal(dummy_process):
        def handler(signum, _frame):
            print('{} got inside handler'.format(os.getpid()))
            print('{} sending {} to {}'.format(os.getpid(), signum,
                                               dummy_process.pid))
            os.kill(dummy_process.pid, signum)

        return handler


    g1 = DummyClass()
    g1.start()
    the_handler = forward_signal(g1)
    signal.signal(signal.SIGTERM, the_handler)
    signal.signal(signal.SIGINT, the_handler)

    g1.join()


if __name__ == '__main__':
    start_the_dummy(GenericDummy)
