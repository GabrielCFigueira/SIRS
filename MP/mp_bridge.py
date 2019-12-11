import socketserver
import socket
import logging, logging.config
import threading
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat

from cryptography.fernet import Fernet
import base64


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('HEIMDALL_MP')

d = {"anakin":["brakes"], "zeus":["oil"]} # d = {"anakin":["radio"], "zeus":["brakes", "oil"]}

encryption_padding =  padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                      )


class MP_Bridge(socketserver.BaseRequestHandler):
    """
    Monotoring protocol forwarding class (aka Heimdall)

    This class just deals with scanning the 1st keyword of the command,
    and then forward it to the responsible provider
    """
    def setup(self):
        """
        Setup connections to both Zeus and Anakin
        """
        global arch_public_key
        logger.info("Connection received from ¯\_(ツ)_/¯")

        # FIXME need to get cert from common location, and cannot be static
        if hasattr(self.server, 'public_key_getter'):
            self.server.public_key = self.server.public_key_getter()
        if hasattr(self.server, 'public_key'):
            self.arch_public_key = self.server.public_key
        else:
            logger.critical('Connection received but no public key available')
            raise Exception("Missing public key")

        logger.info("Connect to architect")

        self.arch = socket.create_connection(('localhost', 7891))
        self.f_lock = threading.Lock()

        logger.info("Connected")


    def handle(self):
        # self.request is the TCP socket connected to the client

        key_refresher = threading.Thread(target=thread_session_key_refresher,
                                         args=[self], daemon=True)
        key_refresher.start()


        logger.info("{}: start handling requests".format(self.client_address[0]))

        bridge = True
        while bridge:
                to_bridge = None

                request = self.request.recv(256)
                to_bridge = request
                logger.debug('Gotta bridge "%s"', to_bridge)

                with self.f_lock:

                    import pdb
                    #pdb.set_trace()
                    if to_bridge == b'':
                        logger.debug('Nothing to bridge, ending')
                        return

                    if to_bridge:
                        enc_to_bridge = self.f.encrypt(to_bridge)
                        bin_mess = len(enc_to_bridge).to_bytes(8, 'big') + enc_to_bridge
                        logger.debug('Sending %s as %s', to_bridge, bin_mess)
                        self.arch.sendall(b'msg')
                        self.arch.sendall(bin_mess)

                    logger.debug('Awaiting a response...')
                    size_response = int.from_bytes(self.arch.recv(8), 'big')
                    enc_response = self.arch.recv(size_response)
                    response = self.f.decrypt(enc_response)
                    logger.debug('Got %s as response', response)
                    self.request.sendall(response)


    def finish(self):
        logger.info("{}: End request bridging".format(self.client_address[0]))
        self.arch.sendall(b'qit')
        self.arch.close()



def session_key_exchange(self):
    # Exchange session key
    with self.f_lock:
        logger.debug('Start kex')
        session_key = Fernet.generate_key()
        f_temp = Fernet(session_key)
        logger.debug('Generated')
        #session_key_enc = session_key
        session_key_enc = self.arch_public_key.encrypt(session_key, encryption_padding)

        self.arch.sendall(b'key')
        self.arch.sendall(session_key_enc)
        enc_challenge = self.arch.recv(100)
        logger.debug('Sent')
        challenge = f_temp.decrypt(enc_challenge)
        print(f'Query: {challenge}')

        self.f = f_temp



def thread_session_key_refresher(self):
    while True:
        session_key_exchange(self)
        time.sleep(5000000)

class ThreadingMP_Bridge(socketserver.ThreadingMixIn, MP_Bridge):
    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", 5555

    # Create the server, binding to localhost on port 5555
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), ThreadingMP_Bridge) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info("Ready to serve")
        server.serve_forever()
