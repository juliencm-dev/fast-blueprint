
# Makefile for building a simple Go application

.PHONY: build test run

build:
	go build -o fast-blueprint main.go

test:
	go test -v ./...

run: build
	./fast-blueprint
