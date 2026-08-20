HUGO ?= hugo
BIND ?= 127.0.0.1
PORT ?=
THEME_DIR ?= ../oink

.DEFAULT_GOAL := dev

.PHONY: b build c check d debug dev s serve

b: build
c: check
d: debug
s: serve

dev:
	HUGO_MODULE_REPLACEMENTS='github.com/pgsty/oink -> $(abspath $(THEME_DIR))' \
		$(HUGO) server --renderToMemory --bind "$(BIND)" $(if $(strip $(PORT)),--port "$(PORT)")

debug: dev

serve:
	HUGO_MODULE_WORKSPACE=off $(HUGO) server --environment production --minify \
		--disableFastRender --disableLiveReload \
		--bind "$(BIND)" $(if $(strip $(PORT)),--port "$(PORT)")

build:
	HUGO_MODULE_WORKSPACE=off $(HUGO) build --gc --minify --cleanDestinationDir

check:
	python3 bin/check_markdown.py README.md archetypes content
	GOWORK=off go mod verify
	HUGO_MODULE_WORKSPACE=off $(HUGO) build --gc --minify --cleanDestinationDir --printPathWarnings --printI18nWarnings --panicOnWarning
	python3 bin/check_internal_links.py public
