HUGO ?= hugo

.PHONY: dev build check

dev:
	$(HUGO) server

build:
	$(HUGO) build --gc --minify --cleanDestinationDir

check:
	go mod verify
	$(HUGO) build --gc --minify --cleanDestinationDir --printPathWarnings --printI18nWarnings --panicOnWarning
	python3 bin/check_internal_links.py public
