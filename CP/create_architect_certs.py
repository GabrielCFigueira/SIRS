import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
import cp_utils


###########
# ROOT
###########
private_key = ec.generate_private_key(
    ec.SECP384R1(), default_backend()
)
public_key = private_key.public_key()
certificate = cp_utils.create_child_cert(private_key, 'Architect Root CA',
                                         public_key, 'Architect Root CA',
                                         ['key_cert_sign', 'crl_sign'],
                                         is_ca=True, child_n=0)

print(isinstance(certificate, x509.Certificate))
b = certificate.public_bytes(Encoding.PEM)
print(b)
with open('oal', 'wb') as outfile:
    outfile.write(b)


###########
# UP
###########
up_priv_key = ec.generate_private_key(
    ec.SECP384R1(), default_backend()
)
up_pub_key = up_priv_key.public_key()
up_certificate = cp_utils.create_child_cert(private_key, 'Architect Root CA',
                                            up_pub_key, 'Architect UP',
                                            ['digital_signature'])

print(isinstance(up_certificate, x509.Certificate))
c = up_certificate.public_bytes(Encoding.PEM)
print(c)
with open('obl', 'wb') as outfile:
    outfile.write(c)


###########
# MP
###########

mp_priv_key = ec.generate_private_key(
    ec.SECP384R1(), default_backend()
)
mp_pub_key = mp_priv_key.public_key()
mp_certificate = cp_utils.create_child_cert(private_key, 'Architect Root CA',
                                            mp_pub_key, 'Architect MP',
                                            ['key_encipherment'])

print(isinstance(mp_certificate, x509.Certificate))

d = mp_certificate.public_bytes(Encoding.PEM)
print(d)
with open('ocl', 'wb') as outfile:
    outfile.write(d)


##################################
#
# Certificate Revocation Lists
#
# We will revoke certificate of UP for example purposes here
#
#################################

crl, _certs = cp_utils.create_crl(private_key, 'Architect Root CA',
                                  [up_certificate])

e = crl.public_bytes(Encoding.PEM)
print(e)
with open('crl_list', 'wb') as outfile:
    outfile.write(e)


print("UP taking into account Root_CA",
        cp_utils.check_certificate('obl', 'oal'))


print("MP taking into account Root_CA",
        cp_utils.check_certificate('ocl', 'oal'))


print("UP taking into account Root_CA + CRL",
        cp_utils.check_certificate('obl', 'oal', 'crl_list'))
