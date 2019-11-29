import time
from multiprocessing import Process
import logging
import socket
import threading
import sys

logging.basicConfig(format='%(message)s', level=logging.INFO)


class GenericDummy(Process):
    def __init__(self):
        super(GenericDummy, self).__init__()
        self.interval = 2 # can be configured
        self.lock = threading.Lock()
        self.port = 5000
        self.state = 0
        self.sock = 0

    def update_state(self):
        pass

    def get_state(self):
        with self.lock:
            return self.state

    def set_state(self, _new):
        pass

    def thread_update(self):
        while True:
            time.sleep(self.interval)
            with self.lock:
                self.state = self.update_state()


    def run(self):
        state_updater = threading.Thread(target=self.thread_update, args=[])
        state_updater.daemon = True
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
                        self.set_state(query[1])


if __name__ == '__main__':
    g1 = GenericDummy()
    g1.start()
    g1.join()
