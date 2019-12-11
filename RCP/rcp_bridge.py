import socketserver
import socket
import logging,logging.config
import addresses


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('HEIMDALL_RCP')


class RCP_Bridge(socketserver.BaseRequestHandler):
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
        try:
            self.zeus = socket.create_connection(addresses.ZEUS_RCP)
        except:
            self.zeus = None
        try:
            self.anakin = socket.create_connection(addresses.ANAKIN_RCP)
        except:
            self.anakin = None
        logger.debug("Connected")


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

            if not destination:
                logger.warn('Request "%s" for unconnected destination', raw_request)
                return

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
                dest = self.zeus

            return dest, rest

        except:
            raise ValueError("Invalid user command")


    def finish(self):
        logger.info("{}: End request bridging".format(self.client_address[0]))
        try:
            self.zeus.sendall(b'quit')
            self.zeus.close()
        except:
            pass
        try:
            self.anakin.sendall(b'quit')
            self.anakin.close()
        except:
            pass

if __name__ == "__main__":

    # Create the server, binding to localhost on port 9999
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(addresses.HEIMDALL_RCP, RCP_Bridge) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info("Ready to serve")
        server.serve_forever()
