---
title: "Build a YUM Repository"
linkTitle: "Build a YUM Repository"
description: "Create a managed RPM repository, apply membership policy, serve it, and configure dnf."
categories: [Tutorial]
tags: [yum, rpm, managed, dist]
url: "/docs/tutorial/yum-repo/"
weight: 100
icon: fa-solid fa-box-open
---

This tutorial creates a new Managed RPM repository. Install SOW and Python 3, and prepare RPM files built for your clients. Use an empty `/srv/sow` directory that your user can create and write to, or substitute another writable path.

## 1. Create the workspace

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
```

`el9` names this RPM package set. You can choose another name; it does not change which
operating systems the packages support.

## 2. Set membership policy

Edit the generated `sow.yml`. This example keeps one version per package and architecture
and excludes debug and LLVM JIT packages:

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  pigsty:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]
targets: {}
```

Check the configuration:

```bash
sow config check
```

`exclude` runs before `limit`. SOW includes `noarch` packages in every enabled architecture view. Keep only CPU architecture names in `architectures`.

## 3. Add RPMs

```bash
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

Replace the input path with your RPM directory. `add` stores accepted packages in the pool, updates membership, and builds the indexes. Review its per-package output: excluded files are reported without failing the whole command.

The public tree has this shape:

```text
/srv/sow/pigsty/
├── pool/...
└── dists/el9/
    ├── x86_64/repodata/...
    └── aarch64/repodata/...
```

RPM indexes point back to `pool/` through relative paths. Serve or copy the complete `pigsty/` tree so clients can download the packages.

## 4. Preview over HTTP

Run this in a separate terminal and leave it running:

```bash
python3 -m http.server --bind 127.0.0.1 --directory /srv/sow/pigsty 8080
```

The preview serves only the Repository root and is reachable from the same host. For a persistent service or clients on other hosts, use [Serve Repositories](/docs/tutorial/serving/).

## 5. Configure dnf

On the Linux host running the preview, save this as `/etc/yum.repos.d/pigsty.repo`. For a remote client, first publish the Repository and substitute its public base URL:

```ini
# /etc/yum.repos.d/pigsty.repo
[pigsty-el9]
name=Pigsty EL9
baseurl=http://127.0.0.1:8080/dists/el9/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

Then refresh and query the repository:

```bash
sudo dnf --disablerepo='*' --enablerepo=pigsty-el9 makecache --refresh
dnf --disablerepo='*' --enablerepo=pigsty-el9 list available
```

This example uses unsigned packages and metadata. Follow [Sign Your Repository](/docs/tutorial/signing/) to enable verification. After the preview, remove this source file and stop the Python server.

## 6. Publish or export

Use [`sow publish`](/docs/tutorial/serving/) for a filesystem or R2 target. It uploads package files and metadata in the order clients need. That guide also covers manual delivery to isolated hosts.

Some mirroring tools, including default `dnf reposync`, reject rpm-md package locations
that traverse to the root pool. Export a self-contained RPM leaf when such a consumer is
required:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/pigsty-el9-x86_64 -r pigsty
```

The RPM Dist must belong to the current Built Generation. In a mixed Repository, check the [export preconditions](/docs/command/export/) first.

The destination must be absent or empty. Export copies package files by default. Use `--hardlink` only on the same filesystem, and keep exported files read-only because they share storage with the source pool.

## Update the repository

```bash
sow add /path/to/new.rpm -r pigsty -d el9
sow check -r pigsty
```

`add` builds the update automatically. With `limit: 1`, the newest version replaces the previous member for each package and architecture. Run `sow build -r pigsty` after changing configuration.

To withdraw a package, preview the selection with `sow rm PACKAGE_NAME -r pigsty -d el9 --check`, then repeat without `--check`. A package name selects all its versions and architectures; use a SHA-256 reference for one package object.

See [Platforms & Integrations](/docs/reference/compatibility/) for tested clients.
