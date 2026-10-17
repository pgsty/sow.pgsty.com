---
title: "Build an APT Repository"
linkTitle: "Build an APT Repository"
description: "Create a managed DEB repository with by-hash indexes and configure an APT client."
categories: [Tutorial]
tags: [apt, deb, managed, dist]
url: "/docs/tutorial/apt-repo/"
weight: 200
icon: fa-solid fa-cube
---

This tutorial creates a new Managed DEB repository. Install SOW and Python 3, and prepare DEB files built for your clients. Use an empty `/srv/sow` directory that your user can create and write to, or substitute another writable path.

## 1. Create the workspace

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new trixie --format deb -r pigsty
```

The Dist name `trixie` becomes the client's `Suites` value. You can choose another name;
it does not change which distributions the packages support.

## 2. Set membership policy

Edit the generated `sow.yml` if you need filtering or version limits:

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  pigsty:
    dists:
      trixie:
        format: deb
        limit: 1
        exclude:
          - kind: [dbgsym, dbg]
targets: {}
```

Then validate it:

```bash
sow config check
```

Use `x86_64` and `aarch64` in configuration. They generate Debian indexes for `amd64`
and `arm64`. Architecture-independent `all` packages enter both views.

## 3. Add DEBs

```bash
sow add /path/to/packages/*.deb -r pigsty -d trixie
sow check -r pigsty
```

Replace the input path with your DEB directory. `add` stores accepted packages once and builds the indexes. The public tree is:

```text
/srv/sow/pigsty/
├── pool/...
└── dists/trixie/
    ├── Release
    └── main/
        ├── binary-amd64/
        │   ├── Packages
        │   ├── Packages.gz
        │   └── by-hash/SHA256/...
        └── binary-arm64/...
```

Paths in `Packages` are relative to the Repository root. Serve the complete `pigsty/`
directory so APT can reach both the indexes and the package files.

## 4. Preview over HTTP

Run this in a separate terminal and leave it running:

```bash
python3 -m http.server --bind 127.0.0.1 --directory /srv/sow/pigsty 8080
```

The preview serves only the Repository root and is reachable from the same host. For a persistent service or clients on other hosts, use [Serve Repositories](/docs/tutorial/serving/).

## 5. Configure APT

On the Linux host running the preview, save this as `/etc/apt/sources.list.d/pigsty.sources`. Use `arm64` in `Architectures` for ARM64 clients. For a remote client, first publish the Repository and substitute its public URL:

```ini
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: http://127.0.0.1:8080
Suites: trixie
Components: main
Architectures: amd64
Trusted: yes
```

Then refresh and query it:

```bash
sudo apt update
apt-cache policy
```

The output should include `trixie/main` as a package source. `Trusted: yes` is used for
this unsigned example. To add signatures, follow [Sign Your Repository](/docs/tutorial/signing/)
to sign metadata, install the public key, and configure `Signed-By`. After the preview,
remove the test source file and stop the Python server.

<span id="6-publish-safely" data-td-print-local></span>

## 6. Publish the repository

Use [`sow publish`](/docs/tutorial/serving/) for a filesystem or R2 target. It uploads packages and indexes before updating `Release` and its signatures. That guide also covers manual delivery to isolated hosts.

## Update the repository

```bash
sow add /path/to/new.deb -r pigsty -d trixie
sow check -r pigsty
```

`add` builds the update automatically. With `limit: 1`, the newest version replaces the previous member for each package and architecture. Run `sow build -r pigsty` after changing configuration.

To withdraw a package, preview the selection with `sow rm PACKAGE_NAME -r pigsty -d trixie --check`, then repeat without `--check`. A package name selects all its versions and architectures; use a SHA-256 reference for one package object.

See [Platforms & Integrations](/docs/reference/compatibility/) for tested clients.
