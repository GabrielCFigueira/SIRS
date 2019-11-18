import socket
import sys
from os import urandom, replace, remove, path
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from bsdiff4 import file_patch
import pdb

chosen_hash = hashes.SHA512()
hasher = hashes.Hash(chosen_hash, default_backend())

pubkey = b''
with open('pub_key', 'rb') as keyfile:
    pubkey = load_pem_public_key(keyfile.read(), default_backend())

SIG_SIZE = 64 # from the docs
CHUNK_SIZE = 4096 # our convention

def apply_patch(target, patch_file=None):
    if not patch_file:
        patch_file = target + '.patch'

    temp = target+'.temp'

    try:
        file_patch(target, temp, patch_file)
        replace(temp, target)
        return True
    except:
        return False
    finally:
        if path.exists(temp):
            remove(temp)

# TODO
def get_installed_version(target_name):
    return b''

def update_installed_version(target_name, new_version):
    pass

# Architect address
HOST, PORT = "localhost", 7890

def try_update(target_name):
    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send update version request
        sock.connect((HOST, PORT))
        hasher = hashes.Hash(chosen_hash, default_backend())

        identifier = b'0123456789' # TODO: make function to associate target_name to 10 byte id
        sock.sendall(b'check|' + identifier)

        info = sock.recv(32)           # 32 chars should be enough
        info_sig = sock.recv(SIG_SIZE) # probably 64 bytes

        hasher.update(info)
        digest = hasher.finalize()

        #pdb.set_trace()

        pubkey.verify(info_sig, digest)

        latest_version = info
        current_version = get_installed_version(target_name)

        if latest_version == current_version:
            return True, False # sucess, no update needed

        nonce = urandom(16) # 128 bits
        print(nonce)

        sock.sendall(b'download_latest|' + nonce)

        # renew hasher TODO encapsulate in function
        hasher = hashes.Hash(chosen_hash, default_backend())

        received_nonce = sock.recv(16)
        bin_size = sock.recv(8)

        hasher.update(received_nonce+bin_size)

        size = int.from_bytes(bin_size, 'big')

        with open(target_name+'.patch', 'wb') as outfile:
            while size > 0:
                chunk = sock.recv(CHUNK_SIZE if CHUNK_SIZE < size else size)
                hasher.update(chunk)
                outfile.write(chunk)
                size -= len(chunk)

        patch_sig = sock.recv(SIG_SIZE)

        digest = hasher.finalize()

        print(digest)

        if nonce != received_nonce:
            raise ValueError('Wrong nonce')

        pubkey.verify(patch_sig, digest)


        try:
            apply_patch(target_name)
            update_installed_version(target_name, latest_version)
        except:
            sock.sendall(b'error|install')
            raise
            # or return False, True
        finally:
            remove(target_name+'.patch')

        return True, True
        sock.close()

if __name__ == '__main__':
    try_update('original')
