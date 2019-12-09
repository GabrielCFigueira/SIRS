import socketserver
import socket
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat

from cryptography.fernet import Fernet
import base64


logging.basicConfig(
    format='%(name)s [%(levelname)s]\t%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d/%M/%Y %H:%M:%S'
)
logger = logging.getLogger('MP_Bridge')

d = {"anakin":["brakes"], "zeus":["oil"]} # d = {"anakin":["radio"], "zeus":["brakes", "oil"]}
f = None


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
        logger.info("Connect to zeus and anakin")
        #self.zeus = socket.create_connection(('localhost',5679))
        self.anakin = socket.create_connection(('localhost',5680))
        logger.info("Connected")

        #self.zeus = socket.create_connection(('zeus',5679))
        #self.anakin = socket.create_connection(('anakin',5679))


    def handle(self):
        # self.request is the TCP socket connected to the client
        logger.debug("{}: start handling requests".format(self.client_address[0]))

        firstMsg = True

        serve = True
        while serve:
            if(firstMsg):
                raw_request = self.request.recv(49)
                #logger.info("{}: Received key {}".format(self.client_address[0], raw_request))

                # Generate a private key for use in the exchange.
                server_private_key = ec.generate_private_key(
                    ec.SECP384R1(), default_backend()
                )
                server_public_key = server_private_key.public_key()

                # Get client public key from the socket.
                client_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP384R1(), raw_request)

                shared_key = server_private_key.exchange(ec.ECDH(), client_public_key)

                # Perform key derivation. This is the session key.
                session_key = HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'handshake data',backend=default_backend()).derive(shared_key)

                # Send key to the sender.
                self.request.sendall(server_public_key.public_bytes(encoding=Encoding.X962, format=PublicFormat.CompressedPoint))


                encoded_s_key = base64.b64encode(session_key)
                f = Fernet(encoded_s_key)

                firstMsg = False




            else:
                raw_request = self.request.recv(256)
                #logger.info("{}: Got request {} for {}".format(self.client_address[0],
                #                                                rest,
                #                                                destination.getpeername()))

                # DECRYPT
                try:
                    msg = f.decrypt(raw_request)
                except:
                    logger.warning("Invalid Token")
                    return

                logger.info("{}: raw_request {} is {}".format(self.client_address[0],
                                                                raw_request,
                                                                msg))
                destination, rest = self.sanitize(msg)

                # send to destination the decrypted request
                destination.sendall(bytes(rest, 'utf-8'))
                logger.info("{}: Forwarded request".format(self.client_address[0]))

                # receive response (for example motor levels)
                response = destination.recv(256)
                logger.info("{}: Forwarding response {}".format(self.client_address[0],
                                                                response))
                # ENCRYPT
                response = f.encrypt(response)
                self.request.sendall(response)


    def sanitize(self, to_sanitize):
        try:
            dest, rest = to_sanitize.decode('ascii').strip().split('|', 1)

            if dest == 'anakin':
                dest = self.anakin
            else:
                dest = self.anakin #self.zeus

            return dest, rest

        except:
            raise ValueError("Invalid user command")


    def finish(self):
        logger.info("{}: End request bridging".format(self.client_address[0]))
        #self.zeus.sendall(b'quit')
        #self.zeus.close()
        self.anakin.sendall(b'quit')
        self.anakin.close()

if __name__ == "__main__":
    HOST, PORT = "localhost", 5555

    # Create the server, binding to localhost on port 5555
    with socketserver.TCPServer((HOST, PORT), MP_Bridge) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info("Ready to serve")
        server.serve_forever()
