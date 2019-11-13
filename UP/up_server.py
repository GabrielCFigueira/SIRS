import socketserver
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils, padding


logging.basicConfig(
    format='%(name)s [%(levelname)s]\t%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger('my_name')


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


            choosen_hash = hashes.SHA256()
            hasher = hashes.Hash(choosen_hash, default_backend())

            if query[0] == 'check':
                response = self.version = get_latest_for(query[1])
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
            sig = private_key.sign(
                    digest,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    utils.Prehashed(choosen_hash)
                )
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
