import socket
import sys
from os import urandom
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
import pdb

chosen_hash = hashes.SHA512()
hasher = hashes.Hash(chosen_hash, default_backend())


pubkey = b''
with open('pub_key', 'rb') as keyfile:
    pubkey = load_pem_public_key(keyfile.read(), default_backend())

SIG_SIZE = 64

def read_file():
    return 0

# Architect address
HOST, PORT = "localhost", 7890

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send update version request
    sock.connect((HOST, PORT))
    sock.sendall(b'check|' + b'0123456789') #10 byte identifier

    info = sock.recv(32)           # 32 chars should be enough
    info_sig = sock.recv(SIG_SIZE) # probably 64 bytes

    hasher.update(info)
    digest = hasher.finalize()

    #pdb.set_trace()

    pubkey.verify(info_sig, digest) #, chosen_hash)
    print('Success!!!!!')

    """
    latest_version, size = [int(s) for s in str(info, 'ascii').split('|')]
    current_version = read_file()

    if latest_version == current_version:
        return True, False # sucess, no update needed

    nonce = urandom(16) # 128 bits
    print(nonce)

    sock.sendall(b'download_latest|' + nonce)


    received_nonce = sock.recv(16)
    size = int.from_bytes(sock.recv(8), 'big')
    patch = sock.recv(size)
    patch_sig = sock.recv(SIG_SIZE)

    # TODO: verify signature and nonce
    # if error, what should it do? just drop it?

    try:
        apply_patch = True
    except OperationError:
        sock.sendall(b'error|install')
        raise
        # or return False, True

    return True, True
    """
    sock.close()
