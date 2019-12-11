import socketserver
import socket
import logging, logging.config
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding

from cryptography.fernet import Fernet
import addresses


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('HEIMDALL_RCP_G')


CHUNK_SIZE = 4096 # our convention
TARGET_PUBKEY_FILE = '/root/.ssh/authorized_keys' #depends on being on vm!!!

class RCP_Greeter(socketserver.BaseRequestHandler):
    """
    This class just deals with getting SSH pubkey from client
    """
    def setup(self):
        """
        Generate ephemeral key
        """
        logger.info("Connection received from (-_-)")
        logger.debug('Generating Fernet key')
        session_key = Fernet.generate_key()
        self.f = Fernet(session_key)

        print('Copy and paste the following key into your app:')
        print(session_key.decode('ascii'))

        logger.info("Connected")


    def handle(self):
        logger.debug('Awaiting SSH public key...')
        size_key = int.from_bytes(self.request.recv(8), 'big')
        enc_pub_key = b''
        while size_key > 0:
            chunk = self.request.recv(CHUNK_SIZE if CHUNK_SIZE < size_key else size_key)
            enc_pub_key += chunk
            size_key -= len(chunk)

        pub_key = self.f.decrypt(enc_pub_key)
        with open(TARGET_PUBKEY_FILE, 'wb+') as outfile:
                outfile.write(pub_key)
        print('Got your public key!')

    def finish(self):
        logger.info('Ending getting SSH public key')



if __name__ == "__main__":

    # Create the server, binding to localhost on port 5555
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(addresses.HEIMDALL_RCP_G, RCP_Greeter) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info("Ready to serve")
        server.serve_forever()
