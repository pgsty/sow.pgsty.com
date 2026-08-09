---
title: "Quick Start"
linkTitle: "Quick Start"
description: "Index a directory of RPM and DEB packages, serve it, and configure a client."
url: "/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
---

Plain mode builds a flat repository in one directory. It does not read `sow.yml`, create
a workspace, or keep a database.

## 1. Prepare a directory

Put RPM and/or DEB files at the directory top level. `sow create` does not recurse and
does not move or rename package files.

```bash
mkdir -p /srv/repo
cp /path/to/packages/*.rpm /path/to/packages/*.deb /srv/repo/
```

If one glob has no matches, copy the formats you actually have instead.

## 2. Generate metadata

```bash
sow create /srv/repo
```

An illustrative mixed-format result is:

```console
created /srv/repo: rpm=1 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

The directory now contains:

```text
/srv/repo/
├── package.rpm
├── package.deb
├── repodata/       # RPM: repomd.xml plus primary, filelists, other
├── Packages        # DEB flat index
└── Packages.gz
```

Plain mode does not generate a DEB `Release`, `InRelease`, or `Release.gpg`. RPM and DEB
metadata are generated in one operation; a parse or render failure prevents the new
indexes from being committed.

## 3. Serve the directory

For a local check, any static file server is sufficient:

```bash
cd /srv/repo
python3 -m http.server --bind 127.0.0.1 8080
```

Verify the protocol entry points from another shell:

```bash
curl --fail http://127.0.0.1:8080/repodata/repomd.xml >/dev/null
curl --fail http://127.0.0.1:8080/Packages.gz >/dev/null
```

Python's server is only a preview. Use a maintained HTTP server for persistent service.

## 4. Configure a client

Replace `REPO_HOST` with the address clients can reach.

{{< tabpane persist="header" >}}
{{< tab header="dnf" lang="ini" >}}
# /etc/yum.repos.d/sow-quickstart.repo
[sow-quickstart]
name=SOW Quick Start
baseurl=http://REPO_HOST:8080/
enabled=1
gpgcheck=0
repo_gpgcheck=0
{{< /tab >}}
{{< tab header="apt" lang="text" >}}
# /etc/apt/sources.list.d/sow-quickstart.list
deb [trusted=yes] http://REPO_HOST:8080/ ./
{{< /tab >}}
{{< /tabpane >}}

Then refresh and install a package:

```bash
# RPM client
sudo dnf makecache
sudo dnf install PACKAGE_NAME

# DEB client
sudo apt update
sudo apt install PACKAGE_NAME
```

The APT source ends in `./` because this is a flat repository. `[trusted=yes]` and the
disabled DNF signature checks are appropriate only for this unsigned quick start. Use a
signed Managed repository when authenticity matters.

## 5. Update the repository

Change the package files and run the same command again:

```bash
sow create /srv/repo
```

The directory contents are the complete Plain-mode state. With unchanged package bytes,
the generated metadata is deterministic and a repeat run reports `noop=true`.

For automation, request the versioned JSON envelope:

```bash
sow create /srv/repo --json
```

## When to use Managed mode

Use Plain mode when the directory already contains exactly what should be published. Use
a [Managed workspace](/docs/start/workspace/) when you need named Dists, architecture
views, membership policy, signed metadata, generations, audit, or publication targets.

See also [`sow create`](/docs/command/create/) and
[Plain Flat Repositories](/docs/feature/plain/).
