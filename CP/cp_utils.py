import datetime
import subprocess
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding

today = datetime.datetime.today()
one_day = datetime.timedelta(1, 0, 0)

def usage_list_to_kwarg(allowed_usages):
    return {u:(u in allowed_usages)
                for u in
                ['digital_signature', 'content_commitment', 'key_encipherment',
                'data_encipherment', 'key_agreement', 'key_cert_sign',
                'crl_sign', 'encipher_only', 'decipher_only']
           }


def create_child_cert(ca_private_key, ca_name,
                      child_pub_key, child_name,
                      usage_list, is_ca=False, child_n=None,
                      past_val=0, future_val=30):

    builder =  (x509.CertificateBuilder()
                    .serial_number(x509.random_serial_number())
                    .public_key(child_pub_key)
                    .subject_name(x509.Name([
                        x509.NameAttribute(NameOID.COMMON_NAME, child_name)]))
                    .issuer_name(x509.Name([
                        x509.NameAttribute(NameOID.COMMON_NAME, ca_name)]))
                    .not_valid_before(today + past_val*one_day)
                    .not_valid_after(today + future_val*one_day)
                    .add_extension(
                        x509.BasicConstraints(ca=is_ca, path_length=child_n),
                        critical=True)
                    .add_extension(
                        x509.KeyUsage(**usage_list_to_kwarg(usage_list)),
                        critical=True)
               )


    child_certificate = builder.sign(
        private_key=ca_private_key, algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    return child_certificate

def create_crl(ca_private_key, ca_name, certificates_to_revoke,
               last_update=0, revocation_date=0, next_update=1):

    real_revocation_date = today + revocation_date*one_day
    # take away certs that do not need revocation because too old
    certs_needed_to_revoke = set([c for c in certificates_to_revoke
                                    if c.not_valid_after > real_revocation_date])

    builder =  (x509.CertificateRevocationListBuilder()
                    .issuer_name(x509.Name([
                        x509.NameAttribute(NameOID.COMMON_NAME, ca_name)]))
                    .last_update(today + last_update*one_day)
                    .next_update(today + next_update*one_day))

    for cert in certs_needed_to_revoke:
        revoked_cert = (x509.RevokedCertificateBuilder()
                            .serial_number(cert.serial_number)
                            .revocation_date(real_revocation_date)
                            .build(default_backend()))
        builder = builder.add_revoked_certificate(revoked_cert)

    crl = builder.sign(
        private_key=ca_private_key, algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    return crl, certs_needed_to_revoke

def check_certificate(to_check, ca_cert=None, crl_file=None):

    ca_check, crl_check = [], []
    if ca_cert:
        ca_check = ['-CAfile', ca_cert]
    if crl_file:
        crl_check = ['-crl_check', '-CRLfile', crl_file]


    command = ['openssl', 'verify', *ca_check, *crl_check, to_check]

    try:
        subprocess.run(command, capture_output=True, check=True)
        return True
    except:
        return False


def read_cert(filename):
    with open(filename, 'rb') as infile:
        cert = x509.load_pem_x509_certificate(infile.read(),
                                            default_backend())
    return cert

def read_crl(filename):
    with open(filename, 'rb') as infile:
        cert = x509.load_pem_x509_crl(infile.read(),
                                      default_backend())
    return cert
