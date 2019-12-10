import os
import socketserver
import socket
import logging,logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('ARCHITECT_CP')

HOST, PORT = "", 5900

certificate_files = {'CRL': 'crl.pem',
                     'UP':  'up_cert.pem',
                     'MP':  'mp_cert.pem'}


class CP_Server(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        logger.debug('Start handling requests from %s', self.client_address)

        request = self.request.recv(4).decode('utf-8').strip()
        logger.debug('Got %s on pipe', request)

        if request not in certificate_files.keys():
            logger.warning('%s requested unexistent "%s"', self.client_address, request)
            return

        filename = certificate_files[request]
        logger.debug('Requested file: %s', filename)
        size = (os.stat(filename).st_size).to_bytes(8, 'big')
        logger.debug('Requested file size: %s', size)

        self.request.sendall(size)
        with open(filename, 'rb') as infile:
            chunk = infile.read(4096)
            while chunk:
                self.request.sendall(chunk)
                chunk = infile.read(4096)


        logger.info('%s: Finished sending %s', self.client_address,
                                                filename)



if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), CP_Server) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info('Ready to serve')
        server.serve_forever()
