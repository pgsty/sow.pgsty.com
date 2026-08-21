---
title: "Installation"
linkTitle: "Installation"
description: "Install SOW from an archive, RPM/DEB package, or source, then verify the binary and filesystem requirements."
categories: [Start]
tags: [install, rpm, deb]
url: "/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW is one executable: there is no service to enable and no runtime language environment.
Release builds target Linux and macOS on `amd64` and `arm64`; Linux also gets RPM and DEB
packages. Windows is not supported.

Use the [Download page](/download/) to select the archive or Linux package that matches
your operating system and architecture. It links each published artifact, its source tag,
and `SHA256SUMS`.

## Install an archive

Download one archive plus `SHA256SUMS`, then verify the matching line before extraction:

```bash
# Linux amd64
grep 'sow_.*_linux_amd64.tar.gz$' SHA256SUMS | sha256sum -c -
tar -xzf sow_*_linux_amd64.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

On macOS, select `darwin_amd64` or `darwin_arm64` and replace `sha256sum -c -` with
`shasum -a 256 -c -`. Without root, install to a directory already on your `PATH`, such
as `~/.local/bin`.

## Install a Linux package

Linux packages use the `1PGSTY` release suffix:

```bash
sudo rpm -Uvh ./sow-*-1PGSTY.x86_64.rpm
sudo apt install ./sow_*-1PGSTY_amd64.deb
```

Choose only the command and architecture that match the host. RPM installs the license at
`/usr/share/licenses/sow/LICENSE`; DEB installs copyright/license metadata under
`/usr/share/doc/sow/`.

## Build from source

The module declares Go 1.26.5. Metadata generation needs no C toolchain. Replace
`vX.Y.Z` with the source tag linked from the Download page:

```bash
git clone https://github.com/pgsty/sow.git
cd sow
set -euo pipefail
SOW_TAG=vX.Y.Z
git checkout "$SOW_TAG"
SOW_VERSION="${SOW_TAG#v}"
CGO_ENABLED=0 go build -trimpath \
  -ldflags="-s -w -X github.com/pgsty/sow/internal/v2cli.Version=${SOW_VERSION}" \
  -o sow ./cmd/sow
sudo install -m 0755 sow /usr/local/bin/sow
```

This uses the release build flags and embeds the selected tag's product version.

## Verify

```bash
sow version
sow help
```

`sow version` reports product version, target OS/architecture, and build Go toolchain.
`sow help` lists the command tree. Each archive also contains `README.md`, `CHANGELOG.md`,
and the Apache-2.0 `LICENSE`.

## Permissions and optional tools

The invoking user needs read access to package inputs and write access to the Plain target
or Managed workspace. Keep Managed workspaces on a local POSIX filesystem: locks, fsync,
safe paths, and atomic rename are part of the correctness contract.

Repository parsing and metadata rendering are in-process. Only two optional paths need
host tools:

- RPM **package** signing requires `rpm` and a working GPG environment;
- an `agent://` metadata key requires `gpg` and `gpg-agent`.

Next: [Quick Start](/docs/start/quickstart/) for Plain mode, or
[First Workspace](/docs/start/workspace/) for Managed mode.
