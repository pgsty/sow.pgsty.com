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

Use Plain mode to build a repository from a directory of packages. It works without a workspace or configuration file. You need SOW, Python 3 for the preview, and at least one RPM or DEB file.

{{% steps %}}

## Prepare a directory {#1-prepare-a-directory}

Create a writable directory. Replace the input paths below and run the copy command for
each package format you have:

```bash
mkdir -p "$HOME/sow-quickstart"
cp /path/to/example.rpm "$HOME/sow-quickstart/"
cp /path/to/example.deb "$HOME/sow-quickstart/"
```

Keep packages at the directory top level; `sow create` does not scan subdirectories.

## Generate metadata {#2-generate-metadata}

```bash
sow create "$HOME/sow-quickstart"
```

With one RPM and one DEB, the output includes:

```text
rpm=1 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

The directory now has indexes beside the original packages:

```text
sow-quickstart/
├── example.rpm
├── example.deb
├── repodata/       # RPM index and metadata
├── Packages        # DEB flat index
└── Packages.gz
```

SOW creates indexes for the formats present. Plain mode does not create APT `Release`, `InRelease`, or `Release.gpg` files. It leaves package names and paths unchanged.

## Start a local server {#3-serve-the-directory}

Run this command in a separate terminal and leave it running:

```bash
python3 -m http.server --bind 127.0.0.1 --directory "$HOME/sow-quickstart" 8080
```

If this host has no APT or DNF client, check the HTTP entry point for the format you added:

```bash
# RPM
curl --fail http://127.0.0.1:8080/repodata/repomd.xml >/dev/null

# DEB
curl --fail http://127.0.0.1:8080/Packages.gz >/dev/null
```

This server is reachable only from the same host. For other clients or a persistent service, follow [Serve Repositories](/docs/tutorial/serving/).

## Configure a local client {#4-configure-a-client}

On a Linux host running the preview server, create the source file for your package manager. These examples use unsigned metadata and disable client signature checks. For signed metadata, use a [Managed workspace](/docs/start/workspace/) and the [signing tutorial](/docs/tutorial/signing/).

{{< tabs group="package-manager" default="dnf" label="Choose a package manager" >}}
{{< tab label="DNF / YUM" value="dnf" >}}
Save this as `/etc/yum.repos.d/sow-quickstart.repo`:

```ini {copy="all"}
[sow-quickstart]
name=SOW Quick Start
baseurl=http://127.0.0.1:8080/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

Refresh the index and install one of your packages:

```bash {copy="all"}
sudo dnf --disablerepo='*' --enablerepo=sow-quickstart makecache
sudo dnf install PACKAGE_NAME
```
{{< /tab >}}
{{< tab label="APT" value="apt" >}}
Save this as `/etc/apt/sources.list.d/sow-quickstart.list`:

```text {copy="all"}
deb [trusted=yes] http://127.0.0.1:8080/ ./
```

The final `./` selects a flat repository. Refresh the index and install one of your packages:

```bash {copy="all"}
sudo apt update
sudo apt install PACKAGE_NAME
```
{{< /tab >}}
{{< /tabs >}}

Replace `PACKAGE_NAME` with a package name from its metadata, not its filename. On macOS, use the HTTP checks above; run package installation on a compatible Linux client.

## Update the repository {#5-update-the-repository}

Add or remove package files, then regenerate the indexes:

```bash
sow create "$HOME/sow-quickstart"
```

Unchanged package files and options produce the same metadata. A repeat run reports `noop=true`.

When replacing another YUM metadata generator, follow [Migrate an Existing YUM Repository](/docs/tutorial/yum-migration/) to preserve the timestamp that cached clients expect.

{{% /steps %}}

When the preview is complete, stop the server with `Ctrl+C` and remove its source file from your client. Keep the package directory if you want to reuse it.

<span id="when-to-use-managed-mode"></span>

## Next

Use a [Managed workspace](/docs/start/workspace/) for named Dists, architecture views, version limits, signed metadata, and publication targets. See [`sow create`](/docs/command/create/) for all Plain options.
