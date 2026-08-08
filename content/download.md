---
title: "Download & Install"
linkTitle: "Download"
description: "Get the SOW binary: release assets, source builds, and release build targets."
url: "/download/"
weight: 20
icon: fa-solid fa-download
---

SOW is one self-contained executable. Archive installation means putting that file on
your `PATH`; there is no service to enable and no state directory until a command needs
one. RPM and DEB release packages provide a conventional Linux installation path.

## Prebuilt binaries

The SOW v0.2.0 GitHub Release is currently a **draft**. Its four Linux/macOS
archives, `1PGSTY` Linux RPM and DEB packages, and `SHA256SUMS` are not publicly
downloadable. Until an operator publishes it on the
[releases page](https://github.com/pgsty/sow/releases), use the source-build path below.
After publication, confirm that the release entry contains the
matching archive and checksum before automating a download, then extract the archive and
move the binary into place:

No Docker or other container image is published for v0.2.0.

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

Without root, install into `~/.local/bin`. SOW itself does not require a privileged
daemon. The invoking user needs read/write access to the Workspace or Plain target and
publication destination, plus read or resolution access to package inputs and signing
references.

## Release build targets

The release pipeline builds with `CGO_ENABLED=0`, avoiding a separately installed cgo
toolchain or language runtime. Binaries still use the operating system's standard ABI and
frameworks. The release artifact targets are:

| OS | `amd64` | `arm64` | Notes |
|---|---|---|---|
| Linux | built | built | primary target |
| macOS (Darwin) | built | built | Intel and Apple Silicon |
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
- [Compatibility](/docs/reference/compatibility/) — current automated evidence and its limits.
