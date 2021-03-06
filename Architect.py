import socket, socketserver
import time
import threading
import logging,logging.config
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import Encoding
from CP.cp_configuration import private_key # generation of private key here
from CP import cp_utils, cp_server
from UP import up_server
from MP import mp_server
import addresses

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ARCHITECT')

def run_a_server(server_class, address, attributes_to_inject={}, logger_suffix=''):
    #logger = logging.getLogger('ARCHITECT_{}'.format(logger_suffix))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(address, server_class) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        for name, value in attributes_to_inject.items():
            setattr(server, name, value)
        logger.info("Ready to serve %s", logger_suffix)
        server.serve_forever()



if __name__ == '__main__':

    # Generate other certificates/keys
    up_priv_key = ec.generate_private_key(
        ec.SECP384R1(), default_backend()
    )
    up_pub_key = up_priv_key.public_key()
    up_certificate = cp_utils.create_child_cert(private_key,
                                                'Architect Root CA',
                                                up_pub_key,
                                                'Architect UP',
                                            ['digital_signature'])

    with open('up_cert.pem', 'wb') as outfile:
        outfile.write(up_certificate.public_bytes(Encoding.PEM))

    mp_priv_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    mp_pub_key = mp_priv_key.public_key()
    mp_certificate = cp_utils.create_child_cert(private_key,
                                                'Architect Root CA',
                                                mp_pub_key,
                                                'Architect MP',
                                            ['key_encipherment'])

    with open('mp_cert.pem', 'wb') as outfile:
        outfile.write(mp_certificate.public_bytes(Encoding.PEM))


    crl, rev_certs = cp_utils.create_crl(private_key, 'Architect Root CA',
                                         [up_certificate, mp_certificate])

    with open('crl.pem', 'wb') as outfile:
        outfile.write(crl.public_bytes(Encoding.PEM))



    # Run a thread to serve Certificate Requests
    certificate_server = threading.Thread(target=run_a_server,
                                          args=[cp_server.CP_Server,
                                        addresses.ARCHITECT_CP, {}, 'CP'],
                                          daemon=True)

    up_props = {'private_key_getter': (lambda: up_priv_key)}
    up_server = threading.Thread(target=run_a_server,
                                 args=[up_server.UP_Server,
                            addresses.ARCHITECT_UP, up_props, 'UP'],
                                          daemon=True)

    mp_props = {'private_key_getter': (lambda: mp_priv_key)}
    mp_server = threading.Thread(target=run_a_server,
                                          args=[mp_server.ThreadingMP_Server, ('', 7891), mp_props, 'MP'],
                                          daemon=True)

    certificate_server.start()
    logger.info("Starting CERT server")
    up_server.start()
    logger.info("Starting UP server")
    mp_server.start()
    logger.info("Starting MP server")
    logger.debug("Start 15 sec sleep before issuing new cert")
    #time.sleep(15)
    input('Press enter for new UP and MP certificates')
    # TODO command line controls
    up_priv_key = ec.generate_private_key(
        ec.SECP384R1(), default_backend()
    )
    up_pub_key = up_priv_key.public_key()
    up_certificate = cp_utils.create_child_cert(private_key,
                                                'Architect Root CA',
                                                up_pub_key,
                                                'Architect UP',
                                            ['digital_signature'])
    with open('up_cert.pem', 'wb') as outfile:
        outfile.write(up_certificate.public_bytes(Encoding.PEM))
    mp_priv_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    mp_pub_key = mp_priv_key.public_key()
    mp_certificate = cp_utils.create_child_cert(private_key,
                                                'Architect Root CA',
                                                mp_pub_key,
                                                'Architect MP',
                                            ['key_encipherment'])

    with open('mp_cert.pem', 'wb') as outfile:
        outfile.write(mp_certificate.public_bytes(Encoding.PEM))
    logger.debug("Issued new UP and MP certs")


    certificate_server.join()
