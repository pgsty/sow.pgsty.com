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

SOW is one executable. It needs no daemon, database service, or language runtime. Release archives support Linux and macOS on `amd64` and `arm64`. Linux also has RPM and DEB packages.

Use the [Download page](/download/) to choose SOW 0.5.0 for your system. Download the selected artifact and `SHA256SUMS` into a separate download directory.

## Install an archive

For Linux amd64, verify the archive, extract it, and install the executable:

```bash
set -euo pipefail
grep '  sow_0.5.0_linux_amd64.tar.gz$' SHA256SUMS | sha256sum -c -
tar -xzf sow_0.5.0_linux_amd64.tar.gz
sudo install -m 0755 sow /usr/local/bin/sow
```

For macOS, select `darwin_amd64` or `darwin_arm64`. Substitute that archive name and use `shasum -a 256 -c -` for the checksum command.

To install without root access:

```bash
mkdir -p "$HOME/.local/bin"
install -m 0755 sow "$HOME/.local/bin/sow"
export PATH="$HOME/.local/bin:$PATH"
```

Add the `export PATH` line to your shell profile to keep it in new sessions.

## Install a Linux package

Verify the downloaded package against its entry in `SHA256SUMS`. Then run the command for your distribution:

```bash
# RPM, x86_64
sudo rpm -Uvh ./sow-0.5.0-1PGSTY.x86_64.rpm

# Debian or Ubuntu, amd64
sudo apt install ./sow_0.5.0-1PGSTY_amd64.deb
```

For ARM64, use the RPM ending in `.aarch64.rpm` or the DEB ending in `_arm64.deb`. Packages install the executable at `/usr/bin/sow`.

## Build from source

Install Go 1.27.1 or newer and Git. The build uses `CGO_ENABLED=0` and needs no C compiler.

```bash
set -euo pipefail
git clone --branch v0.5.0 https://github.com/pgsty/sow.git
cd sow
SOW_BUILD_DIR="$(mktemp -d)"
CGO_ENABLED=0 go build -trimpath \
  -ldflags='-s -w -X github.com/pgsty/sow/internal/v2cli.Version=0.5.0' \
  -o "$SOW_BUILD_DIR/sow" ./cmd/sow
sudo install -m 0755 "$SOW_BUILD_DIR/sow" /usr/local/bin/sow
```

<span id="verify" data-td-print-local></span>

## Verify the installation

```bash
sow version
sow help
```

`version` shows the product version, target operating system and architecture, and Go toolchain. `help` lists commands. Use `sow help COMMAND` for a command's options.

<span id="upgrade-a-03-managed-workspace" data-td-print-local></span>

## Upgrade a Managed workspace from 0.3 or 0.4 {#upgrade-from-04-to-05}

SOW 0.5.0 uses database schema v13. The `schema: sow/v3` configuration and public directory layout stay the same.

1. Stop all workspace writers.
2. Back up the complete workspace with a tool that preserves hard links, such as `rsync -aH` or `tar`. DEB `by-hash` entries use hard links.
3. Install SOW 0.5.0.
4. For each Repository in `sow.yml`, migrate, rebuild, and check:

```bash
sow repo migrate REPOSITORY -C /srv/sow
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

Replace `REPOSITORY` with its configured name. Migration updates the database; the rebuild
applies the current RPM verification and APT metadata rules.

Keep the backup for rollback. Older SOW binaries cannot open the migrated database. See [`sow repo migrate`](/docs/command/repo/#sow-repo-migrate) and the [0.5.0 release notes](/blog/release/sow-v0.5.0/).

## Upgrade a Plain repository

Plain mode has no database to migrate. For an existing YUM repository, follow [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) before changing its generator. Version 0.5 adds `--metadata-timestamp`, but its default is still `0`. Set the timestamp from the repository's publication history so cached YUM clients accept the new index.

<span id="permissions-and-optional-tools" data-td-print-local></span>

## Storage and optional tools

The SOW user needs read access to input packages and write access to the repository. Keep Managed workspaces on a local POSIX filesystem with file locks, `fsync`, and atomic rename.

Package parsing and metadata generation run inside SOW. Optional signing needs these host tools:

| Signing method | Required tools |
|---|---|
| Metadata signing with an OpenPGP key file or key material | None |
| Metadata signing with a GPG key identifier | `gpg` and `gpg-agent` |
| RPM package signing | `rpm` with a working GPG signing setup |

Continue with [Quick Start](/docs/start/quickstart/) for Plain mode or [First Workspace](/docs/start/workspace/) for Managed mode.
