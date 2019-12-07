from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
# Generate a private key for use in the exchange.
client_private_key = ec.generate_private_key(
    ec.SECP384R1(), default_backend()
)
client_public_key = client_private_key.public_key()
server_private_key = ec.generate_private_key(
    ec.SECP384R1(), default_backend()
)
server_public_key = server_private_key.public_key()
# In a real handshake the peer_public_key will be received from the
# other party. For this example we'll generate another private key
# and get a public key from that.

shared_key = client_private_key.exchange(ec.ECDH(), server_public_key)
# Perform key derivation.
derived_key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'handshake data',
    backend=default_backend()
).derive(shared_key)

shared_key_2 = server_private_key.exchange(ec.ECDH(), client_public_key)
derived_key_2 = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'handshake data',
    backend=default_backend()
).derive(shared_key_2)

print(derived_key == derived_key_2)