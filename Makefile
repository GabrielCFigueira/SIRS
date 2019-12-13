

.PHONY: vm local clean cleaner

vm:
	sed -i'.bak' 's/^VMs = False$$/VMs = True/g' `find . -type f -name 'addresses.py'`
	find . -name 'addresses.py.bak' -delete
	sed -i'.bak' 's/^HEIMDALL_TARGET="127.1"$$/HEIMDALL_TARGET="heimdall"/g' RCP/rcp_app.sh
	rm RCP/rcp_app.sh.bak

local:
	sed -i'.bak' 's/^VMs = True$$/VMs = False/g' `find . -type f -name 'addresses.py'`
	find . -name 'addresses.py.bak' -delete
	sed -i'.bak' 's/^HEIMDALL_TARGET="heimdall"$$/HEIMDALL_TARGET="127.1"/g' RCP/rcp_app.sh
	rm RCP/rcp_app.sh.bak

clean:
	touch client_ssh_key* rcp_*.key
	rm `find . -name '*\.pem' ! -name 'root_*\.pem'` client_ssh_key*
	rm rcp_*.key

cleaner: clean
	rm `find -name 'root_*\.pem'
