import socket
import sys
import logging
from os import urandom, replace, remove, path
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from bsdiff4 import file_patch
import addresses
import pdb

chosen_hash = hashes.SHA256()
sign_alg = ec.ECDSA(hashes.SHA256())
hasher = hashes.Hash(chosen_hash, default_backend())


SIG_SIZE = 128 # from the docs
CHUNK_SIZE = 4096 # our convention
NONCE_SIZE = 16 # 128 bits of nonce

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


def try_update(dummy_id, current_version, dummy_file, stop_dummy_callback, pubkey, logger=logging):
    # Create a socket (SOCK_STREAM means a TCP socket)
    logger.debug('Trying to connect to Update Server in %s', addresses.ARCHITECT_UP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send update version request
        #pdb.set_trace()

        try:
            sock.connect(addresses.ARCHITECT_UP)
        except ConnectionRefusedError:
            logger.warning('Unable to connect to Update Server in %s', addresses.ARCHITECT_UP)
            return False, False

        logger.debug('Connection established with Update Server')
        hasher = hashes.Hash(chosen_hash, default_backend())


        # FIXME use nonce
        nonce = urandom(NONCE_SIZE)
        sock.sendall(b'check|' + dummy_id + nonce)

        latest_version = sock.recv(32) # 32 chars should be enough
        received_nonce = sock.recv(NONCE_SIZE)
        info_sig = sock.recv(SIG_SIZE) # probably 64 bytes

        hasher.update(latest_version+received_nonce)
        digest = hasher.finalize()

        logger.debug('Sent     nonce: %s', nonce)
        logger.debug('Received nonce: %s', received_nonce)
        logger.debug('Current version: %s', current_version)
        logger.debug('Latest version:  %s', latest_version)
        logger.debug('Digest: %s', digest)
        logger.debug('Signature: %s', info_sig)


        try:
            pubkey.verify(info_sig, digest, sign_alg)
        except InvalidSignature:
            logger.critical('Signature verification failed when updating %s!', dummy_id)
            return False, False

        if nonce != received_nonce:
            logger.critical('Altered nonce when updating %s', dummy_id)
            return False, False

        if latest_version == current_version:
            logger.debug('Same version, responding and closing coms')
            sock.sendall(b'allok|' + dummy_id)
            return True, False # sucess, no update needed


        logger.debug('New version, continuing')
        # renew hasher
        hasher = hashes.Hash(chosen_hash, default_backend())

        nonce = urandom(NONCE_SIZE) # 128 bits
        sock.sendall(b'download_latest|' + nonce)

        received_nonce = sock.recv(NONCE_SIZE)
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

        try:
            pubkey.verify(patch_sig, digest, sign_alg)
        except InvalidSignature:
            logger.critical('Signature verification failed when updating %s!', dummy_id)
            return False, False


        if nonce != received_nonce:
            logger.critical('Altered nonce when updating %s', dummy_id)
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
    with open('up_cert.pem', 'rb') as infile:
        up_cert = x509.load_pem_x509_certificate(
                                            infile.read(),
                                            default_backend())
    pubkey = up_cert.public_key()
    try_update('testtestte', 'testtesttesttesttesttesttesttest', 'original', lambda: True, pubkey)
