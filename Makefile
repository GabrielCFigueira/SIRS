

.PHONY: clean cleaner

clean:
	rm `find . -name '*\.pem' ! -name 'root_*\.pem'` client_ssh_key*
	rm rcp_*.key

cleaner: clean
	rm `find -name 'root_*\.pem'
