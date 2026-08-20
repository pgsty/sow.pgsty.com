HUGO ?= hugo

.PHONY: dev serve build check

dev:
	HUGO_MODULE_REPLACEMENTS='github.com/pgsty/oink -> $(abspath ../oink)' $(HUGO) server --renderToMemory

serve:
	$(HUGO) server --environment production --minify --disableFastRender --disableLiveReload

build:
	$(HUGO) build --gc --minify --cleanDestinationDir

check:
	go mod verify
	$(HUGO) build --gc --minify --cleanDestinationDir --printPathWarnings --printI18nWarnings --panicOnWarning
	python3 bin/check_internal_links.py public
