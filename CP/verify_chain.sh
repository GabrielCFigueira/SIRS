#!/bin/sh

# To see a certificate in plaintext
# openssl x509 -text -noout -in <certificate file>

# To see a CRL in plaintext
# openssl crl -text -noout -in <CRL file>


openssl verify -CAfile oal obl
openssl verify -CAfile oal ocl

openssl verify -crl_check -CAfile oal -CRLfile crl_list obl


# Expected output:
#$ ./verify_chain.sh
#obl: OK
#ocl: OK
#CN = Architect UP
#error 23 at 0 depth lookup: certificate revoked
#error obl: verification failed
