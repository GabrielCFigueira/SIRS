#!/bin/sh -e


HEIMDALL_TARGET="127.1"
KEY_FILE='client_ssh_key'


if [ ! -f $KEY_FILE ] ;  then
	ssh-keygen -t ed25519 -f $KEY_FILE -N ''
	python3 RCP/rcp_client.py $KEY_FILE.pub
fi
ssh root@$HEIMDALL_TARGET -i $KEY_FILE 'nc 127.1 5678'
