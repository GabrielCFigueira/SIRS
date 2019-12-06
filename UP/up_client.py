import socket
import sys
from os import urandom, replace, remove, path
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from bsdiff4 import file_patch
import pdb

#TODO tothink: use name or just uid? still need to kill a process, and to know a filename from uid

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

# Architect address
HOST, PORT = "localhost", 7890

def try_update(dummy_id, current_version, dummy_file):
    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send update version request
        #pdb.set_trace()
        sock.connect((HOST, PORT))
        hasher = hashes.Hash(chosen_hash, default_backend())

        sock.sendall(b'check|' + dummy_id)

        latest_version = sock.recv(32) # 32 chars should be enough
        info_sig = sock.recv(SIG_SIZE) # probably 64 bytes

        hasher.update(latest_version)
        digest = hasher.finalize()


        pubkey.verify(info_sig, digest)

        if latest_version == current_version:
            sock.sendall(b'allok|' + dummy_id)
            return True, False # sucess, no update needed

        nonce = urandom(16) # 128 bits

        sock.sendall(b'download_latest|' + nonce)

        # renew hasher TODO encapsulate in function
        hasher = hashes.Hash(chosen_hash, default_backend())

        received_nonce = sock.recv(16)
        bin_size = sock.recv(8)

        hasher.update(received_nonce+bin_size)

        size = int.from_bytes(bin_size, 'big')

        with open(dummy_file+'.patch', 'wb') as outfile:
            while size > 0:
                chunk = sock.recv(CHUNK_SIZE if CHUNK_SIZE < size else size)
                hasher.update(chunk)
                outfile.write(chunk)
                size -= len(chunk)

        patch_sig = sock.recv(SIG_SIZE)

        digest = hasher.finalize()

        if nonce != received_nonce:
            raise ValueError('Wrong nonce')
        pubkey.verify(patch_sig, digest)


        try:
            apply_patch(dummy_file)
            sock.sendall(b'allok|' + dummy_id)
        except:
            sock.sendall(b'error|' + dummy_id)
            raise
            # or return False, True
        finally:
            remove(dummy_file+'.patch')
            sock.close()

    return True, True

if __name__ == '__main__':
    try_update('testtestte', 'testtesttesttesttesttesttesttest', 'original')
