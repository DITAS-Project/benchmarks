define PROJECT_HELP_MSG

Usage:
    make help                   show this message
    make clean                  remove intermediate files (see CLEANUP)
    make start                  launch a jupyter server from the local virtualenv
	make bench					perform the behchmakrs
endef
export PROJECT_HELP_MSG

help:
	echo $$PROJECT_HELP_MSG 

fonts:
	for i in images/*.pdf; do echo "$${i}:" >> fonts.log && pdffonts $$i >> fonts.log; done && less fonts.log && rm fonts.log

start:
	jupyter notebook .

CLEANUP = *.pyc .ipynb_checkpoints/ __pycache__

build:
	cd doom && 	CGO_ENABLED=0 go build -a --installsuffix cgo --ldflags="-w -s -X main.Build=$$(git rev-parse --short HEAD)" -o ../bin/doom

bench-berlin:
	cp scripts/config.berlin.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

bench-ideko:
	cp scripts/config.ideko.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

bench-direct:
	cp scripts/config.direct.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

bench-zurich:
	cp scripts/config.zurich.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

bench-zurich-noMon:
	cp scripts/config.zurich.noMonitoring.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

bench:
	cp scripts/config.test.sh scripts/config.sh
	scripts/preflightChecks.sh
	scripts/runBenchmark.sh

prep:
	scripts/prepare.sh


clean:
	rm -rf ${CLEANUP}

.PHONY: help start clean fonts prep bench build
