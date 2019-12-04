import socketserver
import socket
import logging


logging.basicConfig(
    format='%(name)s [%(levelname)s]\t%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d/%M/%Y %H:%M:%S'
)
logger = logging.getLogger('LCP_Bridge')


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
        logger.info("Connected")

        #self.zeus = socket.create_connection(('zeus',5679))
        #self.anakin = socket.create_connection(('anakin',5679))


    def handle(self):
        # self.request is the TCP socket connected to the client
        logger.debug("{}: start handling requests".format(self.client_address[0]))

        serve = True
        while serve:
            raw_request = self.request.recv(256)
            try:
                destination, rest = self.sanitize(raw_request)
            except ValueError:
                logger.info("{}: got invalid request, shutting it down".format(
                                                                self.client_address[0]))
                logger.info("{}: request was: {}".format(self.client_address[0],
                                                         raw_request))
                self.request.shutdown(socket.SHUT_RD)
                self.request.sendall(bytes("Invalid command: ", 'utf-8') + raw_request)
                return # For cleanup

            logger.debug("{}: request {} is {}".format(
                                                                self.client_address[0],
                                                                raw_request,
                                                                rest))

            logger.info("{}: Got request {} for {}".format(self.client_address[0],
                                                            rest,
                                                            destination.getpeername()))

            destination.sendall(bytes(rest, 'utf-8'))
            logger.info("{}: Forwarded request".format(self.client_address[0]))
            response = destination.recv(256)
            logger.info("{}: Forwarding response {}".format(self.client_address[0],
                                                            response))
            self.request.sendall(response)


    def sanitize(self, to_sanitize):
    # TODO: bullet-proof this

        try:
            dest, rest = to_sanitize.decode('ascii').strip().split('|', 1)

            # TODO: maybe invert logic and make it default zeus?
            dest = self.anakin
#           if command in ['motor', 'lock']:
#               dest = self.anakin #zeus
#           elif command == 'read' and opt in ['brake', 'gas', 'direction']:
#               dest = self.anakin #zeus

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
