import socketserver
import logging, logging.config
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.serialization import load_pem_private_key

import pdb
import os

import addresses

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ARCHITECT_MP')

private_key=None
encryption_padding =  padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                      )

class MP_Server(socketserver.BaseRequestHandler):
    """
    Monitor provider
    """
    def setup(self):
        global private_key
        import pdb
        #pdb.set_trace()
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
        # collecting results
        collect = True
        while collect:
            logger.debug('Waiting for results/key exchanges')
            what = self.request.recv(3)
            import pdb
            #pdb.set_trace()
            logger.debug('Got what: %s', what)

            if what == b'key':
                self.f = session_key_exchange(self.request)
                continue
            if what == b'qit':
                return

            size_result = int.from_bytes(self.request.recv(8), 'big')
            print(size_result)
            enc_result = self.request.recv(size_result)
            result = self.f.decrypt(enc_result)
            logger.debug('Got %s as result', result)

            query_res = result.decode('utf-8').strip().split('|')
            for res in query_res:
                logger.info('Received status update: %s', res)

            query = (lambda: 'oil|temp')()
            enc_query = self.f.encrypt(bytes(query, 'utf-8'))
            bin_mess = (len(enc_query)).to_bytes(8, 'big') + enc_query
            self.request.sendall(bin_mess)
            logger.debug('Sent ack')


    def finish(self):
        print('Stop handling request')

def session_key_exchange(heimdall_socket):
    logger.debug('Getting new session key')
    session_key_enc = heimdall_socket.recv(256)
    session_key = private_key.decrypt(session_key_enc, encryption_padding)
    f_temp = Fernet(session_key)


    # Challenge
    # Receive Challenge
    enc_challenge_bridge = heimdall_socket.recv(140)
    # Decrypt challenge_bridge
    challenge_bridge = f_temp.decrypt(enc_challenge_bridge)
    logger.debug('ex ch %s', str(int.from_bytes(challenge_bridge, 'big')))
    # Add 1 to challenge_bridge
    challenge_bridge_1 = (int.from_bytes(challenge_bridge, 'big') + 1).to_bytes(32, 'big')
    # Send challenge_bridge+1
    logger.debug('Sent')
    enc_challenge_bridge_1 = f_temp.encrypt(challenge_bridge_1)
    heimdall_socket.sendall(enc_challenge_bridge_1)
    # Create challenge
    challenge = os.urandom(32)
    # Encrypt challenge
    enc_challenge = f_temp.encrypt(challenge)
    # Send challenge
    heimdall_socket.sendall(enc_challenge)
    # Receive challenge_response
    enc_challenge_response = heimdall_socket.recv(140)
    # Decrypt challenge
    challenge_response = f_temp.decrypt(enc_challenge_response)
    # Verify challenge
    if int.from_bytes(challenge_response, 'big') == int.from_bytes(challenge, 'big') + 1 :
        logger.info('Challenge corret!')
    else:
        return None
    # End of Challenge
    
    return f_temp


class ThreadingMP_Server(socketserver.ThreadingMixIn, MP_Server):
    pass

if __name__ == "__main__":

    # Create the server, binding to localhost on port 7891
    #socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(addresses.ARCHITECT_MP, ThreadingMP_Server) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info('Ready to serve')
        server.serve_forever()
