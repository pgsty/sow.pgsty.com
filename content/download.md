---
title: "Download & Install"
linkTitle: "Download"
description: "Get the SOW binary: prebuilt releases, source builds, and the supported platform matrix."
url: "/download/"
weight: 20
icon: fa-solid fa-download
---

SOW is one static executable. There is no installer, no package to add, no service to
enable, and no state directory until you run a command that needs one. Installing it
means putting a single file on your `PATH`.

## Prebuilt binaries

SOW v0.2.0 is currently staged as a **draft** on the
[GitHub releases page](https://github.com/pgsty/sow/releases). The draft contains four
Linux/macOS archives, `1PGSTY` Linux RPM and DEB packages, and `SHA256SUMS`, but draft
assets are not a public download surface. Until an operator publishes the draft, use the
source-build path below. After publication, confirm that the release entry contains the
matching archive and checksum before automating a download, then extract the archive and
move the binary into place:

No Docker or other container image is published for v0.2.0.

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

Without root, `~/.local/bin` works just as well. SOW never needs elevated privileges for
its own operation.

## Platform matrix

The binary is built with `CGO_ENABLED=0`, so it carries no libc dependency and runs on
any reasonably modern kernel of the matching OS and CPU family.

| OS | `amd64` | `arm64` | Notes |
|---|---|---|---|
| Linux | supported | supported | primary target |
| macOS (Darwin) | supported | supported | Intel and Apple Silicon |
| Windows | — | — | not supported |

Windows is out of scope: SOW depends on POSIX advisory locks and atomic
`rename`. For the same reason, keep repositories on local POSIX filesystems — network
filesystems such as NFS do not provide the locking and durability semantics it relies on.

## Build from source

A Go toolchain is the only build requirement. The project declares **Go 1.26.5** or newer.

```bash
git clone https://github.com/pgsty/sow.git
cd sow
CGO_ENABLED=0 go build -trimpath -o sow ./cmd/sow
```

Because there is no cgo, cross-compiling needs nothing beyond Go itself:

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -o sow-linux-arm64 ./cmd/sow
```

## Verify

```bash
sow version
```

```console
sow 0.2.0 darwin/arm64 go1.26.5
```

The line reports the SOW version, the platform the binary targets, and the Go toolchain
that built it. `sow --version` prints the same string, and `sow help` lists the full
command tree.

## What you do not install

Generating repository metadata never shells out. SOW parses RPM headers and Debian
control files itself, computes its own checksums, and writes `repodata/`, `Packages`, and
`Release` in-process — `createrepo_c`, `dpkg-scanpackages`, `reprepro`, and `modifyrepo_c`
are never invoked.

Only two optional features touch the environment: RPM **package** signing needs `rpm` and
a working GPG setup, and an `agent://` key reference needs a running `gpg-agent`.
Everything else, including `file://` and `env://` metadata signing, runs inside the
binary. See [Installation](/docs/start/install/) for the details.

## Next steps

- [Quick Start](/docs/start/quickstart/) — turn a directory of packages into a servable repository in five minutes.
- [First Workspace](/docs/start/workspace/) — build a curated, multi-architecture repository.
- [Compatibility](/docs/reference/compatibility/) — the tested client matrix.
