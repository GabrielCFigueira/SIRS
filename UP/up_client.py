import socket
import sys
import logging
from os import urandom, replace, remove, path
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
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

def try_update(dummy_id, current_version, dummy_file, stop_dummy_callback, logger=logging):
    # Create a socket (SOCK_STREAM means a TCP socket)
    logger.debug('Trying to connect to Update Server in %s:%s', HOST, PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send update version request
        #pdb.set_trace()

        try:
            sock.connect((HOST, PORT))
        except ConnectionRefusedError:
            logger.warning('Unable to connect to Update Server in %s:%s', HOST, PORT)
            return False, False

        logger.debug('Connection established with Update Server')
        hasher = hashes.Hash(chosen_hash, default_backend())


        # FIXME use nonce
        sock.sendall(b'check|' + dummy_id)

        latest_version = sock.recv(32) # 32 chars should be enough
        info_sig = sock.recv(SIG_SIZE) # probably 64 bytes

        hasher.update(latest_version)
        digest = hasher.finalize()

        logger.debug('Current version: %s', current_version)
        logger.debug('Latest version:  %s', latest_version)
        logger.debug('Digest: %s', digest)
        logger.debug('Signature: %s', info_sig)


        try:
            pubkey.verify(info_sig, digest)
        except InvalidSignature:
            logger.critical('Signature verification failed when updating %s!', dummy_id)
            return False, False


        if latest_version == current_version:
            logger.debug('Same version, responding and closing coms')
            sock.sendall(b'allok|' + dummy_id)
            return True, False # sucess, no update needed


        logger.debug('New version, continuing')
        # renew hasher
        hasher = hashes.Hash(chosen_hash, default_backend())

        nonce = urandom(16) # 128 bits
        sock.sendall(b'download_latest|' + nonce)

        received_nonce = sock.recv(16)
        bin_size = sock.recv(8)
        hasher.update(received_nonce+bin_size)


        logger.debug('Sent     nonce: %s', nonce)
        logger.debug('Received nonce: %s', received_nonce)
        logger.debug('Patch size: %s', bin_size)


        size = int.from_bytes(bin_size, 'big')
        with open(dummy_file+'.patch', 'wb') as outfile:
            while size > 0:
                chunk = sock.recv(CHUNK_SIZE if CHUNK_SIZE < size else size)
                hasher.update(chunk)
                outfile.write(chunk)
                size -= len(chunk)

        patch_sig = sock.recv(SIG_SIZE)

        digest = hasher.finalize()
        logger.debug('Digest: %s', digest)

        if nonce != received_nonce:
            logger.critical('Altered nonce when updating %s', dummy_id)
            return False, False

        try:
            pubkey.verify(patch_sig, digest)
        except:
            logger.critical('Signature verification failed when updating %s!', dummy_id)
            return False, False


        try:
            stop_dummy_callback()
            apply_patch(dummy_file)
            sock.sendall(b'allok|' + dummy_id)
        except Exception as ex:
            logger.warn('Something went wrong %s!', dummy_id)
            logger.warn('Exception %s', ex)
            sock.sendall(b'error|' + dummy_id)
            return False, True # test if right
        finally:
            remove(dummy_file+'.patch')
            sock.close()

    logger.debug('Update completed successfully')
    return True, True

if __name__ == '__main__':
    try_update('testtestte', 'testtesttesttesttesttesttesttest', 'original', lambda: True)
