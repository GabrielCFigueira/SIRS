import socketserver
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import pdb

logging.basicConfig(
    format='%(name)s [%(levelname)s]\t%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger('my_name')

private_key = b''
with open('priv_key', 'rb') as keyfile:
    private_key = load_pem_private_key(keyfile.read(), None, default_backend())

chosen_hash = hashes.SHA512()

class UP_Server(socketserver.BaseRequestHandler):
    """
    Updates provider
    """
    def setup(self):
        logger.info("Connection received from ¯\_(ツ)_/¯")


    def handle(self):
        # self.request is the TCP socket connected to the client

        serve = True
        while serve:
            # TODO: sanitize first
            # TODO: if nonce, it won't split
            query = self.request.recv(16).decode('utf-8') \
                                          .strip() \
                                          .split("|")
            logger.debug("{}: Got {} on the pipe".format(
                                        self.client_address[0],
                                        query))


            hasher = hashes.Hash(chosen_hash, default_backend())

            if query[0] == 'check':
                response = self.version = "ola01234567890123456789012345678" #get_latest_for(query[1])
                #pdb.set_trace()
                response = bytes(response, 'ascii')
            elif query[0] == 'download_latest':
                if not getattr(self, 'version', False):
                    response = b'error:mischeck|'
                else:
                    filename = get_patch_for(self.version)
                    with open(filename, 'rb') as infile:
                        nonce = self.request.recv(16)
                        size = (os.stat(filename).st_size).to_bytes(8, 'big')
                        hasher.update(nonce+size)
                        self.request.sendall(nonce+size)
                        chunk = infile.read(4096)
                        while chunk:
                            hasher.update(chunk)
                            self.request.sendall(chunk)
                            chunk = infile.read(4096)


            if response:
                logger.info("{}: Answering with {}".format(
                                            self.client_address[0],
                                            response))

                self.request.sendall(response)



            logger.info("{}: Generating and sending sig".format(
                                            self.client_address[0]))
            hasher.update(response)
            digest = hasher.finalize()
            sig = private_key.sign(digest) #, ec.ECDSA(utils.Prehashed(chosen_hash)))
            print(sig)
            self.request.sendall(sig)


class ThreadingUP_Server(socketserver.ThreadingMixIn, UP_Server):
    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", 7890

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), ThreadingUP_Server) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info('Ready to serve')
        server.serve_forever()
