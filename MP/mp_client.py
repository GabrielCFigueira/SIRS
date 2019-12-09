import socket
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat

from cryptography.fernet import Fernet
import base64

HOST, PORT = "localhost", 5555
data = " ".join(sys.argv[1:])


if __name__ == "__main__":

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((HOST, PORT))
		# EXCHANGE SESSION KEY
		# Generate a private key for use in the exchange.
		client_private_key = ec.generate_private_key(
	    	ec.SECP384R1(), default_backend()
		)
		client_public_key = client_private_key.public_key()

		# Send the public key to the bridge
		sock.sendall(client_public_key.public_bytes(encoding=Encoding.X962, format=PublicFormat.CompressedPoint))

		# Receive the public key from bridge
		server_public_key = sock.recv(49)
		server_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP384R1(), server_public_key)
		#session_key_2 = sock.recv(1024)

		# Generate the session key
		shared_key = client_private_key.exchange(ec.ECDH(), server_public_key)
		session_key = HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'handshake data',backend=default_backend()).derive(shared_key)
		# EXCHANGE SESSION KEY
		#print(session_key == session_key_2)

		encoded_s_key = base64.b64encode(session_key)
		f = Fernet(encoded_s_key)
		token = f.encrypt(bytes(data + "\n", "utf-8")) # b"anakin|brakes"
		sock.sendall(token)

		response = sock.recv(1024)
		try:
			response = f.decrypt(response)
		except:
			print("Invalid Token")
		print(response)



	print("Sent:     {}".format(data))
	print("Received: {}".format(response))