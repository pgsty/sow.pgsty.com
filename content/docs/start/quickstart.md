---
title: "Quick Start"
linkTitle: "Quick Start"
description: "Index a directory of RPM and DEB packages, serve it, and configure a client."
categories: [Start]
tags: [plain, rpm, deb, cli]
url: "/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
search_keywords: [quick start, getting started, sow create, plain repository, rpm, deb]
search_boost: 1.6
---

Plain mode builds a flat repository in one directory. It does not read `sow.yml`, create
a workspace, or keep a database.

{{% steps %}}

## Prepare a directory {#1-prepare-a-directory}

Put RPM and/or DEB files at the directory top level. `sow create` does not recurse and
does not move or rename package files.

```bash
mkdir -p /srv/repo
cp /path/to/packages/*.rpm /path/to/packages/*.deb /srv/repo/
```

If one glob has no matches, copy the formats you actually have instead.

## Generate metadata {#2-generate-metadata}

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

## Serve the directory {#3-serve-the-directory}

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

## Configure a client {#4-configure-a-client}

Replace `REPO_HOST` with the address clients can reach.

{{< tabs group="package-manager" default="dnf" label="Choose a package manager" >}}
{{< tab label="DNF / YUM" value="dnf" >}}
```ini {copy="all"}
# /etc/yum.repos.d/sow-quickstart.repo
[sow-quickstart]
name=SOW Quick Start
baseurl=http://REPO_HOST:8080/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```
{{< /tab >}}

{{< tab label="APT" value="apt" >}}
```text {copy="all"}
# /etc/apt/sources.list.d/sow-quickstart.list
deb [trusted=yes] http://REPO_HOST:8080/ ./
```
{{< /tab >}}
{{< /tabs >}}

Then refresh and install a package:

{{< tabs group="package-manager" default="dnf" label="Refresh metadata and install" >}}
{{< tab label="DNF / YUM" value="dnf" >}}
```bash {copy="all"}
sudo dnf makecache
sudo dnf install PACKAGE_NAME
```
{{< /tab >}}

{{< tab label="APT" value="apt" >}}
```bash {copy="all"}
sudo apt update
sudo apt install PACKAGE_NAME
```
{{< /tab >}}
{{< /tabs >}}

The APT source ends in `./` because this is a flat repository. `[trusted=yes]` and the
disabled DNF signature checks are appropriate only for this unsigned quick start. Use a
signed Managed repository when authenticity matters.

## Update the repository {#5-update-the-repository}

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

{{% /steps %}}

## When to use Managed mode

Use Plain mode when the directory already contains exactly what should be published. Use
a [Managed workspace](/docs/start/workspace/) when you need named Dists, architecture
views, membership policy, signed metadata, generations, audit, or publication targets.

See also [`sow create`](/docs/command/create/) and
[Plain Flat Repositories](/docs/feature/plain/).
