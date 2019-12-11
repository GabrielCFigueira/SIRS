

.PHONY: vm local clean cleaner

vm:
	sed 's/^VMs = False$$/VMs = True/g' -i $$(find . -name 'addresses.py')
	sed 's/^HEIMDALL_TARGET="127.1"$$/HEIMDALL_TARGET="heimdall"/g' -i RCP/rcp_app.sh

local:
	sed 's/^VMs = True$$/VMs = False/g' -i $$(find . -name 'addresses.py')
	sed 's/^HEIMDALL_TARGET="heimdall"$$/HEIMDALL_TARGET="127.1"/g' -i RCP/rcp_app.sh

clean:
	rm `find . -name '*\.pem' ! -name 'root_*\.pem'` client_ssh_key*
	rm rcp_*.key

cleaner: clean
	rm `find -name 'root_*\.pem'
