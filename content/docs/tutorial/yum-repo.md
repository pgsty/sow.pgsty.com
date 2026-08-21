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

This tutorial creates a new Managed RPM repository. You need a writable
directory, and one or more RPM files.

## 1. Create the workspace

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
```

The Dist name is an identifier chosen by you. SOW does not infer an operating-system
release from `el9`.

## 2. Set membership policy

Edit the generated `sow.yml`. This example keeps one version per package and architecture
and excludes debug packages:

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

Validate every manual edit before writing repository state:

```bash
sow config check
sow config show --all
```

`exclude` runs before `limit`. Neutral `noarch` packages are projected into every enabled
architecture view; they are not listed in `architectures`.

## 3. Add RPMs

```bash
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow status -r pigsty
sow check -r pigsty
```

`add` parses the package headers, stores each accepted package once in the canonical pool,
updates Desired membership, and materializes a new Generation. Excluded inputs are reported
per item and are not command failures.

The public tree has this shape:

```text
/srv/sow/pigsty/
├── pool/...
└── dists/el9/
    ├── x86_64/repodata/...
    └── aarch64/repodata/...
```

The rpm-md `location href` entries reach package bytes in the root `pool/` by relative
paths. Do not copy an architecture directory by itself: it is not a standalone repository.

## 4. Preview over HTTP

For a local preview:

```bash
cd /srv/sow
python3 -m http.server --bind 127.0.0.1 8080
```

Check the entry point from another shell:

```bash
curl --fail http://127.0.0.1:8080/pigsty/dists/el9/x86_64/repodata/repomd.xml >/dev/null
```

Use a maintained HTTP server for persistent service. It must expose the whole `pigsty/`
tree so client-resolved package URLs under `pigsty/pool/` remain reachable.

## 5. Configure dnf

Replace `REPO_HOST` with an address the client can reach:

```ini
# /etc/yum.repos.d/pigsty.repo
[pigsty-el9]
name=Pigsty EL9
baseurl=http://REPO_HOST:8080/pigsty/dists/el9/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
```

Then refresh and query the repository:

```bash
sudo dnf clean metadata
sudo dnf makecache --refresh
dnf --disablerepo='*' --enablerepo=pigsty-el9 list available
```

This configuration is deliberately unsigned. Enable client verification only after
following [Sign Your Repository](/docs/tutorial/signing/).

## 6. Publish or export

Before delivery, require a successful deep check:

```bash
sow check -r pigsty
```

Use [`sow publish`](/docs/tutorial/serving/) for a configured filesystem or R2 target. A
whole-root copy is acceptable only into an offline staging location that is switched into
service atomically; do not run an unordered in-place sync against a live repository.

Some mirroring tools, including default `dnf reposync`, reject rpm-md package locations
that traverse to the root pool. Export a self-contained RPM leaf when such a consumer is
required:

```bash
sow export rpm-leaf el9 x86_64 /srv/export/pigsty-el9-x86_64 -r pigsty
```

The destination must be absent or empty. The export duplicates package bytes by default;
`--hardlink` is an explicit same-filesystem, trusted, read-only optimization.

## Update the repository

```bash
sow add /path/to/new.rpm -r pigsty -d el9
sow rm PACKAGE_NAME -r pigsty -d el9
sow build -r pigsty
sow check -r pigsty
```

`add` and `rm` change Desired membership. `build` is useful after policy or signing
configuration changes. `check` is the publication gate; `status` alone is not.

The automated client and platform scope is listed under
[Platforms & Integrations](/docs/reference/compatibility/).
