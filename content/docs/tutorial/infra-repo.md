---
title: "Build the pigsty-infra Repository"
linkTitle: "Build pigsty-infra"
description: "Turn an existing dual-architecture RPM and DEB package pool into an infra repository, then validate installs, roll updates, promote to Stable, and take monthly snapshots."
url: "/docs/tutorial/infra-repo/"
weight: 500
icon: fa-solid fa-hammer
---

[`pgsty/infra-pkg`](https://github.com/pgsty/infra-pkg) is the upstream build source for Pigsty Infra packages.
This tutorial assumes the dual-architecture RPMs and DEBs already exist and covers the second half of the job: turning that pile of packages into a real, consumable, maintainable SOW repository named `infra`.

## 1. Put the packages under ~/repo

This tutorial uses the fixed path `~/repo` throughout. Copy the existing packages into two input directories:

```bash
mkdir -p ~/repo/packages/rpm ~/repo/packages/deb
cp ~/pgsty/infra-pkg/dist/rpm/*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/*.deb ~/repo/packages/deb/
```

Confirm that all four format-by-architecture cells contain real payloads:

```bash
find ~/repo/packages/rpm -maxdepth 1 -type f -name '*.x86_64.rpm' | wc -l
find ~/repo/packages/rpm -maxdepth 1 -type f -name '*.aarch64.rpm' | wc -l
find ~/repo/packages/deb -maxdepth 1 -type f -name '*_amd64.deb' | wc -l
find ~/repo/packages/deb -maxdepth 1 -type f -name '*_arm64.deb' | wc -l
```

All four results must be greater than zero. At this point, the tree is only an input package pool:

```text
~/repo/
└── packages/
    ├── rpm/                         # x86_64 + aarch64 RPMs
    └── deb/                         # amd64 + arm64 DEBs
```

## 2. Create the infra Repository and two Dists

Initialize a Workspace and create the Repository named `infra`:

```bash
sow init ~/repo
cd ~/repo
sow repo new infra
sow dist new rpm --format rpm -r infra
sow dist new deb --format deb -r infra
```

The model is now fixed:

```text
Repository: infra
├── Dist: rpm    format=rpm    policy=latest
└── Dist: deb    format=deb    policy=latest
```

Open `~/repo/sow.yml` and reduce it to this configuration:

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
sow config show --all -r infra
```

## 3. Ingest once and build once

Update Desired Membership first, then build a single time:

```bash
cd ~/repo
sow add ~/repo/packages/rpm --recursive -r infra -d rpm --skip
sow add ~/repo/packages/deb --recursive -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

Initialization is complete only when `sow check` returns `0`. Verify the formats and architectures that SOW
read from the package headers:

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

Print the actual directories:

```bash
find ~/repo -maxdepth 6 -type d | LC_ALL=C sort
```

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

One path rule is easy to miss and essential to remember: SOW always places Dists below `dists/`. The logical
`infra/rpm` and `infra/deb` channels are therefore served from `/infra/dists/rpm/` and `/infra/dists/deb/`,
while package payloads live in `/infra/pool/`. Always publish or mount the complete `~/repo/infra` tree, never
an individual Dist.

## 5. Serve the repository read-only with Nginx

Use the official `nginx:alpine` image and mount the Repository Root read-only at `/infra`:

```bash
docker network create --internal infra-lab
docker run --detach \
  --name infra-nginx \
  --network infra-lab \
  --publish 8080:80 \
  --volume "$HOME/repo/infra:/usr/share/nginx/html/infra:ro" \
  nginx:alpine
```

Check both metadata entry points directly:

```bash
curl -fsS http://127.0.0.1:8080/infra/dists/rpm/x86_64/repodata/repomd.xml | head
curl -fsS http://127.0.0.1:8080/infra/dists/deb/Release | head
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

This isolated HTTP lab temporarily disables verification. A production service should sign RPM and APT metadata
and remove both `gpgcheck=0` and `Trusted: yes`.

Docker validates the host architecture by default. To run the complete four-cell matrix, repeat each `docker run`
once with `--platform linux/amd64` and once with `--platform linux/arm64`; cross-architecture execution requires
Docker binfmt/QEMU support. Repository inventory and client installation are separate acceptance gates.

## 8. Routine maintenance: add a new version

The normal update operation is `add`, not removing the old package first. Suppose the four new `pg-exporter`
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

> [!WARNING] Removal is only for hard corrections
> Do not begin a normal release with `sow rm`. If a bad package must be withdrawn, use
> `sow ls -r infra -d rpm --json` (or the corresponding `-d deb`) to find its exact SHA-256, run
> `sow rm sha256:... -r infra -d rpm --check`, inspect the plan, then run the same command without
> `--check`. `rm` removes only Dist Membership; conservative `sow gc` handles pool bytes separately. Avoid a bare
> package name that could remove every version and architecture.

## 9. Two retention layers: latest and stable

`limit: 1` makes `rpm` and `deb` good rolling channels but cannot express “keep every formally released version.”
Create two more Dists for that purpose:

```bash
cd ~/repo
sow dist new rpm-stable --format rpm -r infra
sow dist new deb-stable --format deb -r infra
sow config show --all -r infra -d rpm-stable -d deb-stable
```

The new Dists default to `limit: 0`, which means retain every version. The resulting policy is:

| Dist | Format | `limit` | Role |
|---|---|---:|---|
| `rpm` | RPM | 1 | RPM latest |
| `deb` | DEB | 1 | DEB latest |
| `rpm-stable` | RPM | 0 | Accumulate promoted RPMs |
| `deb-stable` | DEB | 0 | Accumulate promoted DEBs |

Stable does not automatically resurrect every historical object that happens to remain in the pool. It starts
accumulating versions that you explicitly promote from this point forward.

## 10. Promote latest into stable

SOW 0.3.0 does not yet expose a dedicated `promote` command. The reliable current procedure is to freeze writers,
export the exact source Dist Membership, and add those objects to the target Dist. Inputs come directly from
`infra/pool`; SOW verifies and reuses each existing Package Object without repackaging it or storing a second copy.

First require clean source state and save the promotion manifests:

```bash
cd ~/repo
sow check -r infra
mkdir -p ~/repo/manifests

sow ls -r infra -d rpm --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-latest-202608.list
sow ls -r infra -d deb --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-latest-202608.list
```

Pause writes to `rpm` and `deb` until promotion finishes, then reuse the pool objects:

```bash
cd ~/repo
(
  set -e
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
sow config show --all -r infra -d rpm-202608 -d deb-202608
```

Pause stable writes during the snapshot window and first persist its exact Membership as manifests:

```bash
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
  set -e
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

Also retain the complete verified Repository Generation so later GC treats it as a safety root:

```bash
sow retain add "$(sow status -r infra --json | jq -r '.result.built_generation')" -r infra
sow retain ls -r infra
```

`retain` protects a whole Repository Generation for recovery and GC; the fixed client-visible URLs are still
provided by the `rpm-202608` and `deb-202608` Dists. SOW 0.3.0 does not enforce Dist immutability, so never running
`add` or `rm` against snapshot Dists after creation is part of the operating contract.

## 12. Client address map

One Nginx service and one shared `infra/pool` support every channel:

| Channel | dnf `baseurl` | APT `URIs` / `Suites` |
|---|---|---|
| latest | `http://infra-nginx/infra/dists/rpm/$basearch/` | `http://infra-nginx/infra` / `deb` |
| stable | `http://infra-nginx/infra/dists/rpm-stable/$basearch/` | `http://infra-nginx/infra` / `deb-stable` |
| 2026-08 | `http://infra-nginx/infra/dists/rpm-202608/$basearch/` | `http://infra-nginx/infra` / `deb-202608` |

Run the final acceptance checks:

```bash
cd ~/repo
sow dist ls -r infra
sow status -r infra
sow check -r infra
```

The result is not a disposable demo directory. It is a real Infra Repository that can continue ingesting packages,
promoting releases, and producing monthly snapshots: `rpm/deb` move quickly, `rpm-stable/deb-stable` accumulate
formal history, monthly Dists provide fixed endpoints, and every view reuses the same immutable package objects.

Stop the temporary service when the lab is complete:

```bash
docker rm --force infra-nginx
docker network rm infra-lab
```
