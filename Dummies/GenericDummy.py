import time
import os
import signal
from multiprocessing import Process
import logging
import logging.config
import socket
import threading
import sys

logging.config.fileConfig('logging.conf')


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
        logger = logging.getLogger(self.name)
        logger.debug('State update thread started')
        while True:
            time.sleep(self.interval)
            with self.lock:
                new_state = self.update_state()
                logger.info("Updating state from '%s' to '%s'", self.state, new_state)
                #print("Updating state from {} to {}".format(self.state, new_state))
                self.state = new_state

    def set_a_new_state_carefully(self, new):
        logger = logging.getLogger(self.name)
        with self.lock:
            new_state = self.set_state(new)
            logger.info("Changing state from '%s' to '%s'", self.state, new_state)
            #print("Changing state from {} to {}".format(self.state, new_state))
            self.state = new_state


    def run(self):
        logger = logging.getLogger(self.name)
        logger.info('Starting up')
        state_updater = threading.Thread(target=self.thread_update, args=[],
                                         daemon=True)
        state_updater.start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.debug('Trying to bind on port %s', self.port)
            self.sock.bind(('127.0.0.1', self.port))
            self.sock.listen(1)
            logger.debug('Started to listen on %s', self.sock.getsockname())
            conn, addr = self.sock.accept()
            with conn:
                logger.info('Received connection from %s', addr)
                while True:
                    query = conn.recv(16).decode('utf-8').rstrip().split('|')
                    logger.info("Got '%s' on the pipe", query)
                    if query[0] == 'read':
                        response = bytes(self.get_state(), 'ascii')
                    elif query[0] == 'kill':
                        logger.info('Sending ack and shutting down')
                        conn.sendall(b'ack')
                        sys.exit(0)
                    elif query[0] == 'set':
                        self.set_a_new_state_carefully(query[1])
                        response = b'ack'
                    elif hasattr(self, query[0]):
                        response = bytes(str(getattr(self, query[0])), 'ascii')
                    else:
                        response = b'commanderror'

                    logger.info("Answering with %s", response)
                    conn.sendall(response)

def start_the_dummy(DummyClass):

    def forward_signal(dummy_process):
        def handler(signum, _frame):
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
