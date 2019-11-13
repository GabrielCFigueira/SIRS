import socketserver
import logging
from responsability import deal_with_it, my_name


logging.basicConfig(
    format='%(name)s [%(levelname)s]\t%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger(my_name)


class LCP_Provider(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def setup(self):
        logger.info("Connection received from ¯\_(ツ)_/¯")


    def handle(self):
        # self.request is the TCP socket connected to the client

        serve = True
        while serve:
            query = self.request.recv(256).decode('utf-8') \
                                          .strip() \
                                          .split("|")
            logger.info("{}: Got {} on the pipe".format(
                                        self.client_address[0],
                                        query))

            if query[0] == 'quit':
                return

            response = deal_with_it(query)

            logger.info("{}: Answering with {}".format(
                                        self.client_address[0],
                                        response))

            self.request.sendall(bytes(response + '\n', 'utf-8'))



if __name__ == "__main__":
    HOST, PORT = "localhost", 5679

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), LCP_Provider) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info('Ready to serve')
        server.serve_forever()
