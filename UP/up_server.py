import socketserver
import logging, logging.config
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from .up_versions import get_latest_version, get_patch_file
import pdb
import os

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ARCHITECT_UP')

chosen_hash = hashes.SHA256()
sign_alg = ec.ECDSA(hashes.SHA256())


class UP_Server(socketserver.BaseRequestHandler):
    """
    Updates provider
    """
    def setup(self):
        global private_key
        logger.info("Connection received from ¯\_(ツ)_/¯")

        # FIXME need to get cert from common location, and cannot be static
        if hasattr(self.server, 'private_key_getter'):
            self.server.private_key = self.server.private_key_getter()
        if hasattr(self.server, 'private_key'):
            private_key = self.server.private_key
        else:
            logger.critical('Connection received but no private key available')
            raise Exception("Missing private key")


    def handle(self):
        # self.request is the TCP socket connected to the client
        serve = True
        while serve:
            #pdb.set_trace()
            response, hashing = None, False
            query = self.request.recv(16).decode('utf-8') \
                                          .strip() \
                                          .split("|")

            logger.info('%s: Received %s', self.client_address, query)

            hasher = hashes.Hash(chosen_hash, default_backend())

            if query[0] == 'check':
                self.name = query[1]
                response = self.version = get_latest_version(query[1])
                logger.info('%s: Latest version: %s', self.client_address, self.version)
                nonce = self.request.recv(16)
                response = bytes(response, 'ascii') + nonce
            elif query[0] == 'download_latest':
                if not getattr(self, 'name', False):
                    logger.warn('%s: Download latest without knowing name', self.client_address)
                    response = b'error:mischeck|'
                elif not getattr(self, 'version', False):
                    logger.warn('%s: Download latest without knowing version', self.client_address)
                    response = b'error:mischeck|'
                else:
                    hashing = True
                    filename = get_patch_file(self.name, self.version)
                    logger.info('%s: Sending patch "%s"', self.client_address, filename)
                    nonce = self.request.recv(16)
                    size = (os.stat(filename).st_size).to_bytes(8, 'big')

                    logger.debug('Nonce: %s', nonce)
                    logger.debug('Patch size: %s', size)

                    hasher.update(nonce+size)
                    self.request.sendall(nonce+size)
                    with open(filename, 'rb') as infile:
                        chunk = infile.read(4096)
                        while chunk:
                            hasher.update(chunk)
                            self.request.sendall(chunk)
                            chunk = infile.read(4096)

            elif query[0] == 'error':
                logger.warn('%s: Error on interaction with component %s', self.client_address,
                                                                          query[1])
                serve = False
            elif query[0] == 'allok':
                logger.info('Successful interaction with component %s', query[1])
                serve = False
            else:
                logger.warning('Unexpected message: %s, stopping interaction', query)
                serve = False



            if response:
                logger.debug("%s: Sending %s",self.client_address, response)

                hasher.update(response)
                self.request.sendall(response)

            if hashing or response:
                digest = hasher.finalize()
                sig = private_key.sign(digest, sign_alg)

                logger.debug('%s: Digest: %s', self.client_address, digest)
                logger.debug('%s: Signature: %s', self.client_address, sig)

                self.request.sendall(sig)


class ThreadingUP_Server(socketserver.ThreadingMixIn, UP_Server):
    pass

if __name__ == "__main__":
    HOST, PORT = "", 7890

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), ThreadingUP_Server) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info('Ready to serve')
        server.serve_forever()
