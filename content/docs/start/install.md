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

The [Download page](/download/) provides SOW 0.9.0 packages, archives, and checksums.
Download your chosen artifact and `SHA256SUMS` into a separate download directory.

## Install an archive

For Linux amd64, verify the archive, extract it, and install the executable:

```bash
set -euo pipefail
grep -F '  sow_0.9.0_linux_amd64.tar.gz' SHA256SUMS | sha256sum -c -
tar -xzf sow_0.9.0_linux_amd64.tar.gz
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
sudo rpm -Uvh ./sow-0.9.0-1PGSTY.x86_64.rpm

# Debian or Ubuntu, amd64
sudo apt install ./sow_0.9.0-1PGSTY_amd64.deb
```

For ARM64, use the RPM ending in `.aarch64.rpm` or the DEB ending in `_arm64.deb`. Packages install the executable at `/usr/bin/sow`.

## Build from source

Install Go 1.27.4 or newer and Git. The build uses `CGO_ENABLED=0` and needs no C compiler.

```bash
set -euo pipefail
git clone --branch v0.9.0 https://github.com/pgsty/sow.git
cd sow
SOW_BUILD_DIR="$(mktemp -d)"
CGO_ENABLED=0 go build -trimpath \
  -ldflags='-s -w -X github.com/pgsty/sow/internal/v2cli.Version=0.9.0' \
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

<span id="upgrade-to-060" data-td-print-local></span>

<span id="upgrade-to-061" data-td-print-local></span>

<span id="upgrade-to-070" data-td-print-local></span>

<span id="upgrade-to-071" data-td-print-local></span>

<span id="upgrade-to-080" data-td-print-local></span>

## Upgrade to 0.9.0 {#upgrade-to-090}

Workspaces on 0.5.0 through 0.8.0 already use database schema v13. You can keep your `sow/v3` configuration and public URLs. Interrupted 0.7.1 local GC plans that contain an empty `manifest` array now resume directly under 0.9.0.

> [!WARNING]
> Review any publication target configured with `max_cache_ttl: 0s` before upgrading. Starting in SOW 0.9.0, new target GC grace records follow `max_cache_ttl` directly without a 30-day floor, so superseded objects with `0s` TTL may become eligible at the next target GC. Previously recorded later `NotBefore` deadlines remain effective.

SOW 0.6.1 and older versions reject `sow.yml` files that use `passfile`; remove `passfile` keys before downgrading.

1. Stop all workspace writers.
2. Back up the complete workspace with a tool that preserves hard links, such as `rsync -aH` or `tar`.
3. Review configured targets for `max_cache_ttl: 0s` and adjust `max_cache_ttl` via `sow publish TARGET --rebind` if clients need a longer retention window.
4. Install SOW 0.9.0.
5. Build and check each Repository in `sow.yml` (or `sow.yaml`):
{.steps .td-steps-compact}

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

Replace `REPOSITORY` with its configured name. A current repository produces a no-op build.
An unchanged build keeps its Generation and metadata timestamps.
New builds record one publication time and reuse it during recovery.

### Workspaces from 0.3 or 0.4 {#upgrade-from-04-to-05}

These workspaces need migration before the first build. After backing up the workspace and installing 0.9.0, run:

```bash
sow repo migrate REPOSITORY -C /srv/sow
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

Repeat these commands for each Repository. Migration updates the database; the rebuild applies the current RPM verification and APT metadata rules.
Keep the backup for rollback to a version that uses an older schema.
See [`sow repo migrate`](/docs/command/repo/#sow-repo-migrate) and the [0.9.0 release notes](/blog/release/sow-v0.9.0/).

## Upgrade a Plain repository

Plain mode has no database to migrate. For an existing YUM repository, follow [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) before changing its generator. The `--metadata-timestamp` default remains `0`. Set the timestamp from the repository's publication history so cached YUM clients accept the new index.

<span id="permissions-and-optional-tools" data-td-print-local></span>

## Storage and optional tools

The SOW user needs read access to input packages and write access to the repository. Keep Managed workspaces on a local POSIX filesystem with file locks, `fsync`, and atomic rename.

Package parsing and metadata generation run inside SOW. Optional signing needs these host tools:

| Signing method | Required tools |
|---|---|
| Metadata signing with an OpenPGP key file or key material | None |
| Metadata signing with a GPG key identifier | `gpg` and `gpg-agent` |
| RPM package signing | `rpm` with a working GPG signing setup |
{.wide .expand}

Continue with [Quick Start](/docs/start/quickstart/) for Plain mode or [First Workspace](/docs/start/workspace/) for Managed mode.
