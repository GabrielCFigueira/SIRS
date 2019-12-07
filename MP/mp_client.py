import socket
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat

HOST, PORT = "localhost", 5678
data = " ".join(sys.argv[1:])


def exchange_skey():
	private_key = ec.generate_private_key(
	    ec.SECP384R1(), default_backend()
	)
	# Generate a private key for use in the exchange.
	server_private_key = parameters.generate_private_key()

	#COMMUNICATE to get sahred key
	#...
	#pub_key = ...

	shared_key = server_private_key.exchange(pub_key) # shared_key = server_private_key.exchange(peer_private_key.public_key())

	derived_key = HKDF(
	    algorithm=hashes.SHA256(),
	    length=32,
	    salt=None,
	    info=b'handshake data',
	    backend=default_backend()
	).derive(shared_key)

	return shared_key


if __name__ == "__main__":
	# Generate a private key for use in the exchange.
	client_private_key = ec.generate_private_key(
    	ec.SECP384R1(), default_backend()
	)
	client_public_key = client_private_key.public_key()
	print(client_private_key)


    # Create a socket (SOCK_STREAM means a TCP socket)
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
	    # Connect to server and send data
	    sock.connect((HOST, PORT))

	    print(len(client_public_key.public_bytes(encoding=Encoding.X962, format=PublicFormat.CompressedPoint)))
	    sock.sendall(client_public_key.public_bytes(encoding=Encoding.X962, format=PublicFormat.CompressedPoint))
	    #key_response = str(sock.recv(4096), "utf-8")
	    server_public_key = sock.recv(49)
	    server_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP384R1(), server_public_key)
	    #key_response.decode('utf-8').strip().split('|', 1)
	    shared_key = client_private_key.exchange(ec.ECDH(), server_public_key)
	    session_key = HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'handshake data',backend=default_backend()).derive(shared_key)

	    """encMsg = data #sign.data with ks, etc...
	    sock.sendall(bytes(data, "utf-8"))

		# Receive data from the server and shut down
	    received = str(sock.recv(1024), "utf-8")

	print("Sent:     {}".format(data))
	print("Received: {}".format(received))"""