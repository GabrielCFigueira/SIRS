#!/bin/sh -e


HEIMDALL_TARGET='127.1'
KEY_FILE='client_ssh_key'


ssh-keygen -t ed25519 -f $KEY_FILE -N ''
python3 RCP/rcp_client.py $KEY_FILE.pub
ssh -v root@$HEIMDALL_TARGET -i $KEY_FILE.pub
