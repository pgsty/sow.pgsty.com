---
title: "SOW v0.2.0"
linkTitle: "SOW v0.2.0"
date: 2026-08-08
author: "Ruohang Feng"
description: "SOW v0.2.0 provides Plain and Managed RPM/DEB repositories, verified generations, signing, publication, retention, GC, and RPM leaf export."
categories: [release]
tags: [Release, sow]
weight: 10
url: "/blog/release/sow-docs-launch/"
---

SOW 0.2.0 is a self-contained RPM and DEB repository manager from
[Pigsty](https://pigsty.io). Release artifacts target Linux and macOS as single Go
executables.

## Two operating modes

**Plain mode** indexes RPM and DEB files already present at one directory's top level:

```bash
sow create /srv/repo
```

It writes `repodata/`, `Packages`, and `Packages.gz` in place. Plain mode has no
Workspace, state database, generations, or DEB `Release` signing.

**Managed mode** owns package membership and lifecycle:

```bash
mkdir -p /srv/sow && cd /srv/sow
sow init .
sow repo new pigsty
sow dist new el9 --format rpm -r pigsty
sow add /path/to/packages/*.rpm -r pigsty -d el9
sow check -r pigsty
```

Each accepted package body is stored once beneath `pool/`. RPM and APT client views live
beneath `dists/` and are materialized as immutable Generations.

## Lifecycle controls

Managed repositories include:

- strict `sow/v3` configuration and explicit membership policy;
- RPM metadata, APT metadata, and optional RPM package signing;
- cheap `status` plus nine-layer `check` for publication gating;
- recoverable filesystem and R2 publication attempts;
- explicit retained Generations and reachability-based local GC;
- standalone `rpm-leaf` export for consumers that reject parent-relative rpm-md paths.

The canonical Managed tree must be delivered as a complete repository. Use `sow publish`
for configured targets or stage a whole-root copy offline before an atomic switch. Do not
update a live repository file by file.

## Compatibility evidence

The active test suite proves clean-room current-CLI builds for both formats, a Plain APT
consumer on Ubuntu 22.04, RPM detached-signature behavior in AlmaLinux 8/9/10 probes, and
an isolated S3-compatible provider fixture. Those probes do not by themselves establish a
complete current Managed DNF/APT or R2 CLI acceptance gate.

See [Compatibility](/docs/reference/compatibility/) for the exact claim boundary and
[Quick Start](/docs/start/quickstart/) for a fresh installation path.
