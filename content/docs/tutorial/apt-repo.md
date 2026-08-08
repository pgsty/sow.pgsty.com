---
title: "Build an APT Repository"
linkTitle: "Build an APT Repository"
description: "Create a managed DEB repository with by-hash indexes and configure an APT client."
url: "/docs/tutorial/apt-repo/"
weight: 200
icon: fa-solid fa-cube
---

This tutorial creates a new Managed DEB repository. You need SOW 0.2.0, a writable
directory, and one or more DEB files.

## 1. Create the workspace

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new trixie --format deb -r pigsty
```

The Dist name becomes the APT suite. It is an identifier chosen by you; SOW does not infer
distribution semantics from `trixie`.

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
sow config show --all
```

SOW stores canonical architecture families in configuration and renders Debian names in
the repository: `x86_64` becomes `amd64`, `aarch64` becomes `arm64`, and neutral `all`
packages are included in both views.

## 3. Add DEBs

```bash
sow add /path/to/packages/*.deb -r pigsty -d trixie
sow status -r pigsty
sow check -r pigsty
```

Accepted package bytes are stored once. The public tree is:

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

Package paths beneath `pool/` are grouped by normalized source package. `Packages` uses
archive-root-relative `Filename` values. SOW writes SHA-256 by-hash copies and advertises
them from `Release`.

## 4. Preview over HTTP

For a local preview:

```bash
cd /srv/sow
python3 -m http.server --bind 127.0.0.1 8080
```

Check the entry points:

```bash
curl --fail http://127.0.0.1:8080/pigsty/dists/trixie/Release >/dev/null
curl --fail http://127.0.0.1:8080/pigsty/dists/trixie/main/binary-amd64/Packages.gz >/dev/null
```

Use a maintained HTTP server for persistent service and expose the complete `pigsty/`
tree.

## 5. Configure APT

Replace `REPO_HOST` with an address the client can reach. For an unsigned test repository,
use a deb822 source with explicit trust:

```ini
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: http://REPO_HOST:8080/pigsty
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

`Trusted: yes` disables authenticity checking and is suitable only for a controlled test.
For a signed repository, remove that line and configure a keyring:

```ini
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/pigsty-archive-keyring.gpg
```

Follow [Sign Your Repository](/docs/tutorial/signing/) before enabling `Signed-By`.

## 6. Publish safely

Require a successful deep check before delivery:

```bash
sow check -r pigsty
```

Use [`sow publish`](/docs/tutorial/serving/) for a configured filesystem or R2 target. If
you use another transport, copy the entire repository into an offline staging location and
switch it into service atomically. Do not update a live `dists/` tree file by file: clients
may observe metadata and package state from different generations.

## Update the repository

```bash
sow add /path/to/new.deb -r pigsty -d trixie
sow rm PACKAGE_NAME -r pigsty -d trixie
sow build -r pigsty
sow check -r pigsty
```

Use `build` after policy or signing configuration changes. Use `check`, not `status` alone,
as the publication gate.

The active automated client proof is intentionally narrower than this Managed workflow;
see [Compatibility](/docs/reference/compatibility/) before making a platform support claim.
