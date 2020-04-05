CC=buildozer
CFLAGS=android release

build:
	$(CC) $(CFLAGS)

clean:
	$(CC) appclean

update:
	git pull
	git push

sign:
	./sign.sh

www:
	python -m SimpleHTTPServer 8000
