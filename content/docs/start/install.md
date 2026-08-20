---
title: "Install SOW"
linkTitle: "Installation"
description: "Download a prebuilt binary or build from source, then verify the install."
url: "/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW ships as one self-contained executable. Archive installation means putting that file
on your `PATH`; RPM and DEB release packages provide a conventional Linux path. There is
no service to enable and no state directory until a command needs one.

## Release build targets

The release pipeline builds with `CGO_ENABLED=0`, avoiding a separately installed cgo
toolchain or language runtime. Binaries still use the operating system's standard ABI and
frameworks. The release artifact targets are:

| OS | `amd64` | `arm64` |
|---|---|---|
| Linux | built | built |
| macOS (Darwin) | built | built |

Windows is not supported. SOW relies on POSIX advisory locks and atomic
`rename`, and it is only tested on local POSIX filesystems — network filesystems such as
NFS do not provide the locking and durability semantics it depends on.

> [!NOTE] Filesystem requirement
> Build a [managed workspace](/docs/start/workspace/) on a local POSIX filesystem so locks,
> fsync, and atomic rename retain their contract. The committed public `pool/ + dists/` tree
> uses no view-local hardlink aliases and can be copied or published normally.

## Download a release

The SOW v0.2.0 GitHub Release is currently a **draft**. Its four Linux/macOS archives,
`1PGSTY` Linux RPM and DEB packages, and `SHA256SUMS` are not publicly downloadable.
Until an operator publishes it on the
[releases page](https://github.com/pgsty/sow/releases), build from source below. After
publication, confirm that the release entry contains the
matching archive and checksum before automating a download, then move the extracted
binary onto your `PATH`:

No Docker or other container image is published for v0.2.0.

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

If you do not have root, install into `~/.local/bin`. SOW does not require a privileged
daemon. The invoking user needs read/write access to the Workspace or Plain target and
publication destination, plus read or resolution access to package inputs and signing
references.

## Build from source

Building requires Go 1.26.5 or newer. Clone the repository and build the `cmd/sow`
entrypoint:

```bash
git clone https://github.com/pgsty/sow.git
cd sow
CGO_ENABLED=0 go build -trimpath -o sow ./cmd/sow
```

Set `GOOS` and `GOARCH` to cross-compile; because there is no cgo, cross-building needs
no toolchain beyond Go itself:

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -o sow-linux-arm64 ./cmd/sow
```

## Verify the install

```bash
sow version
```

```console
sow 0.2.0 darwin/arm64 go1.26.5
```

The version line reports the SOW version, the platform the binary was built for, and the
Go toolchain that built it. `sow --version` prints the same string.

To see the full command tree:

```bash
sow help
```

Every command has its own help page — `sow help create`, `sow help dist new`, and so on —
which lists the exact flags that command accepts. Flags that are not in a command's
matrix are rejected rather than ignored.

## External tools

Nothing about generating repository metadata calls out to another program. SOW parses
RPM headers and Debian control files itself, computes checksums itself, and writes
`repodata/`, `Packages`, and `Release` in-process. `createrepo_c`, `dpkg-scanpackages`,
`reprepro`, and `modifyrepo_c` are never invoked.

Two optional features do use the environment:

| Feature | Requires | Why |
|---|---|---|
| RPM **package** signing — `sow create --sign-with`, or a managed `packages.mode` of `fill` / `always` | `rpm` and a working GPG environment | Package payload signatures are produced by `rpm --addsign` against a private staged copy |
| Metadata signing with an `agent://<fingerprint>` key reference | `gpg` with a running `gpg-agent` | The private key stays in the agent and never reaches SOW |

Metadata signing with a `file://` or `env://` key reference is done in-process and needs
no external GPG. See [Signing](/docs/tutorial/signing/) for the full setup.

## Next steps

- [Quick Start](/docs/start/quickstart/) — publish a directory of packages in five minutes.
- [First Workspace](/docs/start/workspace/) — build a curated, multi-architecture repository.
- [Core Concepts](/docs/start/concepts/) — the model behind both paths.
