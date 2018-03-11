build: Dockerfile
	docker build -t digilist/latex-microservice .
run:
	docker run --rm -ti -p 9999:9999 digilist/latex-microservice
default: build
