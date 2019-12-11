import multiprocessing
import threading
import subprocess
import socket, socketserver
import time, datetime
import logging, logging.config
import addresses
from RCP import rcp_bridge, rcp_greeter
from MP import mp_bridge
from CP import cp_utils

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('HEIMDALL')

CHUNK_SIZE = 4096
cert_store = {'MP': [threading.Lock(), None]}

def careful_getter(which):
    with cert_store[which][0]:
        return cert_store[which][1].public_key()

def run_a_server(server_class, address, attributes_to_inject={}, logger_suffix=''):
    logger = logging.getLogger('HEIMDALL_{}'.format(logger_suffix))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(address, server_class) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        for name, value in attributes_to_inject.items():
            setattr(server, name, value)
        logger.info("Ready to serve")
        server.serve_forever()

def thread_certificate_checking():
    logger = logging.getLogger('HEIMDALL_CP')

    def get_pem_from_arch(what, filename, date_for_update=datetime.datetime.today()):

        if date_for_update < datetime.datetime.today():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Connect to server and send update version request
                #pdb.set_trace()
                try:
                    logger.debug('Getting new %s', what)
                    sock.connect(addresses.ARCHITECT_CP)
                    sock.sendall(bytes(what, 'utf-8'))
                    size = int.from_bytes(sock.recv(8), 'big')
                    with open(filename, 'wb') as outfile:
                        while size > 0:
                            chunk = sock.recv(CHUNK_SIZE if CHUNK_SIZE < size else size)
                            outfile.write(chunk)
                            size -= len(chunk)
                    logger.debug('Finished getting %s', what)
                except (ConnectionRefusedError, BrokenPipeError):
                    logger.warning('Unable to connect to Certificate Server in %s', 'architect')
                    # compatibility hack
                    class Object(object):
                        pass
                    res = Object()
                    res.next_update = date_for_update
                    res.not_valid_after = date_for_update
                    return res
        else:
            logger.debug('Not getting new %s', what)

        if what == 'CRL':
            crl = cp_utils.read_crl(filename)
            return crl
        else:
            cert = cp_utils.read_cert(filename)
            return cert



    # here I just want to fetch it
    mp_cert = get_pem_from_arch('MP', 'heimdall_current_mp_cert.pem')
    crl_next_update = datetime.datetime.today()
    while True:
        cert_lock = cert_store['MP'][0]
        with cert_lock:
            crl = get_pem_from_arch('CRL', 'heimdall_current_crl.pem', crl_next_update)
            while not cp_utils.check_certificate('heimdall_current_mp_cert.pem', 'root_cert.pem', 'heimdall_current_crl.pem'):
                logger.warning('No valid mp certificate')
                time.sleep(5)
                mp_cert = get_pem_from_arch('MP', 'heimdall_current_mp_cert.pem')
                crl = get_pem_from_arch('CRL', 'heimdall_current_crl.pem', crl.next_update)
            logger.info('Got valid certificates')
            cert_store['MP'][1] = mp_cert
            crl_next_update = crl.next_update


        nearest_datetime = crl.next_update if crl.next_update < mp_cert.not_valid_after else mp_cert.not_valid_after
        time.sleep(((nearest_datetime-datetime.datetime.today())/2).seconds)


if __name__ == '__main__':

    # CP
    logger.info('Starting Certificate Protocol thread')
    cp = threading.Thread(target=thread_certificate_checking, args=[], daemon=True)
    cp.start()

    # Run a thread to serve RCP
    heimdal_rcp = threading.Thread(target=run_a_server,
                                   args=[rcp_bridge.RCP_Bridge,
                                   addresses.HEIMDALL_RCP, {}, 'RCP'],
                                   daemon=True)

    # Run a thread to serve RCP Greeter (SSH pubkey exchange)
    heimdal_rcp_g = threading.Thread(target=run_a_server,
                                   args=[rcp_greeter.RCP_Greeter,
                                   addresses.HEIMDALL_RCP_G, {}, 'RCP_G'],
                                   daemon=True)

    # Run a thread to serve MP
    mp_props = {'public_key_getter': (lambda: careful_getter('MP'))}
    heimdal_mp = threading.Thread(target=run_a_server,
                                   args=[mp_bridge.ThreadingMP_Bridge,
                                   addresses.HEIMDALL_MP, mp_props, 'MP'],
                                   daemon=True)

    logger.debug('Starting RCP bridging and greeting service')
    heimdal_rcp.start()
    heimdal_rcp_g.start()
    logger.debug('Starting MP bridging service')
    heimdal_mp.start()
    #input("Press enter to kill them all")
    time.sleep(5000)


    #heimdall_rcp.join()
