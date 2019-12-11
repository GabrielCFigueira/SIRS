import socket
import sys,os
import addresses
from cryptography.fernet import Fernet

PUBKEY_FILE = sys.argv[1]

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect(addresses.HEIMDALL_RCP_G)


    f = Fernet(bytes(input('Paste here the given key:'), 'ascii'))
    with open(PUBKEY_FILE, 'rb') as infile:
        enc_pub_key = f.encrypt(infile.read())
        size = len(enc_pub_key).to_bytes(8, 'big')
        print('Encrypted key size:', size)
        sock.sendall(size+enc_pub_key)
