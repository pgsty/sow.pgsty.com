---
title: "Install SOW"
linkTitle: "Installation"
description: "Download a prebuilt binary or build from source, then verify the install."
url: "/docs/start/install/"
weight: 100
icon: fa-solid fa-download
---

SOW ships as a single static executable. Installing it means putting one file somewhere
on your `PATH`. There is no package to install, no service to enable, and no state
directory created until you run a command that needs one.

## Supported platforms

The binary is built with `CGO_ENABLED=0`, so it has no libc dependency and runs on any
reasonably modern kernel of the matching OS and CPU family.

| OS | `amd64` | `arm64` |
|---|---|---|
| Linux | supported | supported |
| macOS (Darwin) | supported | supported |

Windows is not supported. SOW relies on POSIX advisory locks, hardlinks, and atomic
`rename`, and it is only tested on local POSIX filesystems — network filesystems such as
NFS do not provide the locking and durability semantics it depends on.

{{% alert title="Filesystem requirement" color="info" %}}
In [managed mode](/docs/start/workspace/), each architecture view is projected from the
package pool with hardlinks, so a repository's `pool/` and `dists/` must live on the same
filesystem. SOW fails loudly rather than silently falling back to copying. Plain mode has
no such requirement.
{{% /alert %}}

## Download a release

Prebuilt binaries for every supported platform are published on the
[GitHub releases page](https://github.com/pgsty/sow/releases). Download the archive that
matches your OS and architecture, extract it, and move the binary onto your `PATH`:

```bash
tar -xzf sow_*.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

If you do not have root on the machine, `~/.local/bin` works just as well — SOW never
needs elevated privileges for its own operation.

## Build from source

Building requires only a Go toolchain. Clone the repository and build the `cmd/sow`
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
sow 0.2.0-dev darwin/arm64 go1.26.5
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
