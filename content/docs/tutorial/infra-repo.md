---
title: "Build the pigsty-infra Repository"
linkTitle: "Build pigsty-infra"
description: "Turn an existing dual-architecture RPM and DEB package pool into an infra repository, then validate installs, roll updates, promote to Stable, and take monthly snapshots."
categories: [Tutorial]
tags: [yum, rpm, managed, publish]
url: "/docs/tutorial/infra-repo/"
weight: 500
icon: fa-solid fa-hammer
---

[`pgsty/infra-pkg`](https://github.com/pgsty/infra-pkg) is the upstream build source for Pigsty Infra packages.
This tutorial uses already-built RPMs and DEBs for x86-64 and ARM64. It creates an `infra` Repository with rolling channels, stable releases, and monthly snapshots. Install SOW, `jq`, and Docker first. The installation examples use `pg-exporter`; include that package and any dependencies not already in the client images.

## 1. Put the packages under ~/repo

Use a new `~/repo` directory for this workspace. Copy packages from your `infra-pkg` checkout into two input directories:

```bash
mkdir -p ~/repo/packages/rpm ~/repo/packages/deb
cp ~/pgsty/infra-pkg/dist/rpm/*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/*.deb ~/repo/packages/deb/
```

Include both x86-64 and ARM64 packages. Step 3 checks their formats and architectures
from package metadata.

## 2. Create the infra Repository and two Dists

Initialize a Workspace and create the Repository named `infra`:

```bash
sow init ~/repo
cd ~/repo
sow repo new infra
sow dist new rpm --format rpm -r infra
sow dist new deb --format deb -r infra
```

Set `limit: 1` for both Dists in `~/repo/sow.yml`:

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  infra:
    dists:
      rpm:
        format: rpm
        limit: 1
      deb:
        format: deb
        limit: 1
```

`limit: 1` keeps only the newest version for each package name and native architecture. The `rpm` and `deb`
Dists are therefore rolling latest channels while still retaining both x86-64 and ARM64.

```bash
sow config check
```

## 3. Ingest once and build once

Import both package formats, then build their indexes together:

```bash
cd ~/repo
sow add ~/repo/packages/rpm --recursive -r infra -d rpm --skip
sow add ~/repo/packages/deb --recursive -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

After `sow check` succeeds, list the formats and architectures read from package metadata:

```bash
sow ls -r infra -d rpm -d deb --json |
  jq -r '.result.packages | group_by(.format + "/" + .canonical_arch)[] |
    "\(.[0].format)\t\(.[0].canonical_arch)\t\(length) packages"'
```

The output must include at least:

```text
deb     aarch64   ... packages
deb     x86_64    ... packages
rpm     aarch64   ... packages
rpm     x86_64    ... packages
```

SOW reports canonical architecture names, so DEB `amd64/arm64` appear here as `x86_64/aarch64`.

## 4. Read the generated filesystem tree

The important structure is:

```text
~/repo/
├── sow.yml                            # configuration; never serve it
├── .sow/                              # database, locks, recovery; never serve it
├── packages/                          # original input pool; archive as desired
│   ├── rpm/
│   └── deb/
└── infra/                             # complete public Repository Root
    ├── pool/                          # one shared payload pool for RPM and DEB
    └── dists/
        ├── rpm/
        │   ├── x86_64/repodata/
        │   └── aarch64/repodata/
        └── deb/
            ├── Release
            └── main/
                ├── binary-amd64/
                └── binary-arm64/
```

SOW places all Dists under `dists/` and packages under `pool/`. Publish or mount the complete `~/repo/infra` tree so every Dist can reach its package files.

## 5. Serve the repository read-only with Nginx

Use the official `nginx:alpine` image and mount the Repository Root read-only at `/infra`:

```bash
docker network create --internal infra-lab
docker run --detach \
  --name infra-nginx \
  --network infra-lab \
  --publish 127.0.0.1:8080:80 \
  --volume "$HOME/repo/infra:/usr/share/nginx/html/infra:ro" \
  nginx:alpine
```

Nginx can see only `~/repo/infra`; it cannot see `sow.yml` or `.sow/`, and it cannot modify the repository.

## 6. Install an RPM from only infra on EL9

The Rocky Linux 9 container below is attached to the `--internal` network. The script removes every preconfigured
repository and enables only `infra`, so a successful installation cannot fall back to a public mirror.

```bash
docker run --rm --interactive --network infra-lab rockylinux:9 bash -s <<'ROCKY'
set -euxo pipefail

rm -f /etc/yum.repos.d/*.repo
cat >/etc/yum.repos.d/infra.repo <<'REPO'
[infra]
name=Pigsty Infra RPM
baseurl=http://infra-nginx/infra/dists/rpm/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
REPO

dnf clean all
dnf --disablerepo='*' --enablerepo=infra makecache
dnf --disablerepo='*' --enablerepo=infra install -y pg-exporter
rpm -q --qf '%{NAME}\t%{VERSION}-%{RELEASE}\t%{ARCH}\n' pg-exporter
command -v pg_exporter
ROCKY
```

An RPM `baseurl` must point to a concrete architecture view. dnf expands `$basearch` to `x86_64` or `aarch64`.

## 7. Install a DEB from only infra on Ubuntu 24.04

APT points `URIs` at the Repository Root and uses the Dist name `deb` as `Suites`:

```bash
docker run --rm --interactive --network infra-lab ubuntu:24.04 bash -s <<'UBUNTU'
set -euxo pipefail

rm -f /etc/apt/sources.list
rm -f /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources
cat >/etc/apt/sources.list.d/infra.sources <<'SOURCE'
Types: deb
URIs: http://infra-nginx/infra
Suites: deb
Components: main
Trusted: yes
SOURCE

apt-get clean
apt-get update
apt-get install -y --no-install-recommends pg-exporter
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' pg-exporter
command -v pg_exporter
UBUNTU
```

The lab uses unsigned repositories. Follow [Sign Your Repository](/docs/tutorial/signing/) to enable `repo_gpgcheck=1` for RPM metadata and `Signed-By` for APT. Use `gpgcheck=1` when RPM package signatures are also available. Remove `Trusted: yes` from the signed APT source.

Docker containers use the host architecture by default. To test the other architecture,
add `--platform linux/amd64` or `--platform linux/arm64` to the corresponding `docker run`.
Cross-architecture execution requires binfmt/QEMU support.

## 8. Routine maintenance: add a new version

To update the repository, run `add` with the new packages. Suppose the four new `pg-exporter`
payloads are ready:

```bash
cp ~/pgsty/infra-pkg/dist/rpm/pg-exporter-*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/pg-exporter_*.deb ~/repo/packages/deb/

cd ~/repo
sow add ~/repo/packages/rpm/pg-exporter-*.rpm -r infra -d rpm --skip
sow add ~/repo/packages/deb/pg-exporter_*.deb -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

Because the latest Dists have `limit: 1`, the new version wins and the old version automatically leaves that
Dist's Desired Membership. The old bytes are not deleted immediately, and relaxing policy later does not make
the old membership reappear automatically.

Rerun the EL9 and Ubuntu clients from sections 6 and 7, refresh metadata, then install or upgrade to complete
the update acceptance test.

To withdraw a bad package, use `sow ls -r infra -d rpm --json` to find its SHA-256. Preview with `sow rm sha256:DIGEST -r infra -d rpm --check`, then repeat without `--check`. Use `-d deb` for DEBs. A SHA-256 reference selects one package object; a bare name selects all its versions and architectures. `sow gc` handles unused pool files separately.

## 9. Two retention layers: latest and stable

`limit: 1` makes `rpm` and `deb` good rolling channels but cannot express “keep every formally released version.”
Create two more Dists for that purpose:

```bash
cd ~/repo
sow dist new rpm-stable --format rpm -r infra
sow dist new deb-stable --format deb -r infra
sow config show -r infra -d rpm-stable -d deb-stable
```

The new Dists default to `limit: 0`, which means retain every version. The resulting policy is:

| Dist | Format | `limit` | Role |
|---|---|---:|---|
| `rpm` | RPM | 1 | RPM latest |
| `deb` | DEB | 1 | DEB latest |
| `rpm-stable` | RPM | 0 | Accumulate promoted RPMs |
| `deb-stable` | DEB | 0 | Accumulate promoted DEBs |

Stable accumulates the versions you explicitly promote after creating the Dists.

## 10. Promote latest into stable

Promote packages by adding the source Dist's pool files to the target Dist. SOW verifies and reuses the existing package objects, so promotion adds no second copy. Pause other repository writers before exporting the manifests. Resume them after promotion finishes.

First require clean source state and save the promotion manifests:

```bash
set -euo pipefail
cd ~/repo
sow check -r infra
mkdir -p ~/repo/manifests

sow ls -r infra -d rpm --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-latest-202608.list
sow ls -r infra -d deb --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-latest-202608.list
```

Add the recorded pool objects to the stable Dists:

```bash
cd ~/repo
(
  set -euo pipefail
  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d rpm-stable --skip
  done < ~/repo/manifests/rpm-latest-202608.list

  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d deb-stable --skip
  done < ~/repo/manifests/deb-latest-202608.list

  sow build -r infra -d rpm-stable -d deb-stable
  sow check -r infra
)
```

Each `add` should report `reused`. If the loop stops midway, the source Dists are unchanged; correct the failure
and rerun the same manifest. Over subsequent promotions, `rpm/deb` retain only the latest version while
`rpm-stable/deb-stable` accumulate release history.

## 11. Take the 2026-08 snapshot from stable

A client-visible monthly snapshot is another pair of Dists:

```bash
cd ~/repo
sow dist new rpm-202608 --format rpm -r infra
sow dist new deb-202608 --format deb -r infra
sow config show -r infra -d rpm-202608 -d deb-202608
```

Pause other repository writers while creating the snapshot. First save the stable package lists:

```bash
set -euo pipefail
sow check -r infra
sow ls -r infra -d rpm-stable --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-stable-202608.list
sow ls -r infra -d deb-stable --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-stable-202608.list
```

Add those manifests to the corresponding snapshot Dists:

```bash
cd ~/repo
(
  set -euo pipefail
  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d rpm-202608 --skip
  done < ~/repo/manifests/rpm-stable-202608.list

  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d deb-202608 --skip
  done < ~/repo/manifests/deb-stable-202608.list

  sow build -r infra -d rpm-202608 -d deb-202608
  sow check -r infra
)
```

To keep this build after you eventually remove the snapshot Dists, also retain the
current Repository Generation:

```bash
sow retain add "$(sow status -r infra --json | jq -r '.result.built_generation')" -r infra
sow retain ls -r infra
```

`retain` stores this build's metadata and protects its package files from garbage collection.
Clients still use the snapshot Dists. SOW does not make these Dists read-only; keep their
membership and effective configuration unchanged to preserve their contents.

## 12. Client address map

One Nginx service and one shared `infra/pool` support every channel:

| Channel | dnf `baseurl` | APT `URIs` / `Suites` |
|---|---|---|
| latest | `http://infra-nginx/infra/dists/rpm/$basearch/` | `http://infra-nginx/infra` / `deb` |
| stable | `http://infra-nginx/infra/dists/rpm-stable/$basearch/` | `http://infra-nginx/infra` / `deb-stable` |
| 2026-08 | `http://infra-nginx/infra/dists/rpm-202608/$basearch/` | `http://infra-nginx/infra` / `deb-202608` |

Use `sow dist ls -r infra` to see all six Dists.

The rolling Dists keep the latest packages, stable Dists accumulate promoted releases, and monthly Dists keep the selected snapshot. All views share the same package pool.

Stop the temporary service when the lab is complete:

```bash
docker rm --force infra-nginx
docker network rm infra-lab
```
