

.PHONY: clean cleaner

clean:
	rm `find . -name '*\.pem' ! -name 'root_*\.pem'`

cleaner: clean
	rm `find -name 'root_*\.pem'
