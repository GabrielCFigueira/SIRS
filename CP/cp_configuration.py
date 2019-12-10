
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from .cp_utils import create_child_cert

SIG_ALG = ec.ECDSA(hashes.SHA512())


try:
    with open('root_priv_key.pem', 'rb') as infile:
        private_key = serialization.load_pem_private_key(
                                            infile.read(),
                                            None,
                                            default_backend())
    with open('root_cert.pem', 'rb') as infile:
        root_cert = x509.load_pem_x509_certificate(
                                            infile.read(),
                                            default_backend())
    test_sig = private_key.sign(b'anicetest', SIG_ALG)
    root_cert.public_key().verify(test_sig, b'anicetest', SIG_ALG)

    print('Reusing stored private key')
except:
    print('Could not load private key. Generating and saving new')
    private_key = ec.generate_private_key(
        ec.SECP384R1(), default_backend()
    )
    public_key = private_key.public_key()
    certificate =          create_child_cert(private_key,
                                             'Architect Root CA',
                                             public_key,
                                             'Architect Root CA',
                                             ['key_cert_sign',
                                             'crl_sign'],
                                             is_ca=True,
                                             child_n=0)

    with open('root_cert.pem', 'wb') as outfile:
        outfile.write(certificate.public_bytes(Encoding.PEM))
    with open('root_priv_key.pem', 'wb') as outfile:
        outfile.write(private_key.private_bytes(Encoding.PEM,
                                                PrivateFormat.PKCS8,
                                                NoEncryption()))


