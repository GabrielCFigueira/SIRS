import socketserver
import socket
import logging,logging.config


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('HEIMDALL_RCP')


class LCP_Bridge(socketserver.BaseRequestHandler):
    """
    Control protocol forwarding class

    This class just deals with scanning the 1st keyword of the command,
    and then forward it to the responsible provider
    """
    def setup(self):
        """
        Setup connections to both Zeus and Anakin
        """
        logger.info("Connect to zeus and anakin")
        #self.zeus = socket.create_connection(('localhost',5679))
        self.anakin = socket.create_connection(('localhost',5679))
        logger.debug("Connected")

        #self.zeus = socket.create_connection(('zeus',5679))
        #self.anakin = socket.create_connection(('anakin',5679))


    def handle(self):
        # self.request is the TCP socket connected to the client
        logger.debug('Start handling requests from %s', self.client_address)

        serve = True
        while serve:
            raw_request = self.request.recv(256)
            logger.debug('Got %s on pipe', raw_request)
            try:
                destination, rest = self.sanitize(raw_request)
            except ValueError:
                logger.warning('Got invalid request from %s, ending connection',
                                                                self.client_address)
                logger.warning('Request was %s', raw_request)
                self.request.shutdown(socket.SHUT_RD)
                self.request.sendall(bytes("Invalid command: ", 'utf-8') + raw_request)
                return # For cleanup

            logger.info('Request "%s" for %s', rest, destination.getpeername())

            destination.sendall(bytes(rest, 'utf-8'))
            logger.debug('Request sent, waiting for response')
            response = destination.recv(256)
            logger.info('Response: %s', response)
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
    HOST, PORT = "localhost", 5678

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), LCP_Bridge) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info("Ready to serve")
        server.serve_forever()
