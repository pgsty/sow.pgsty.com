---
title: "Build an APT Repository"
linkTitle: "Build an APT Repository"
description: "Create a managed DEB repository with a Debian-style pool, by-hash indexes, and both deb822 and legacy client configurations."
url: "/docs/tutorial/apt-repo/"
weight: 200
icon: fa-solid fa-cube
---

This tutorial builds a managed APT repository: a Debian-style package pool grouped by source
package, one index per architecture, `by-hash` index copies so clients never race a rebuild, and
client configuration in both the modern deb822 format and the legacy one-liner.

Plan for about fifteen minutes.

## Before you start

You need SOW installed ([Installation](/docs/start/install/)), some `.deb` files, and a
directory you can write to.

This tutorial continues from [Build a YUM Repository](/docs/tutorial/yum-repo/) by adding a
second Dist to the same `pigsty` repository — one pool, two package ecosystems. If you are
starting fresh, run these three commands first and then continue from Step 1:

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
sow repo new pigsty
```

The DEB packages used below cover `amd64`, `arm64`, and `all`, and include one package
(`libpq5`) whose `Source` field differs from its binary name — that is what makes the pool
layout visible.

## Step 1: Create the DEB Dist

A Dist has exactly one format. Name it after the suite your clients will write in their sources
line — `trixie`, `noble`, `bookworm`, whatever you are targeting.

```bash
sow dist new trixie --format deb -r pigsty
```

```console
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=5 dirty=false
```

The Dist inherited the workspace architectures. SOW stores architectures as canonical CPU
families (`x86_64`, `aarch64`) and renders them under their ecosystem names in the DEB tree, so
`x86_64` becomes `binary-amd64` and `aarch64` becomes `binary-arm64`. You never have to convert
between the two spellings yourself.

Look at what an empty Dist produced:

```bash
find pigsty/dists/trixie -type f | sort
```

```console
pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
pigsty/dists/trixie/main/binary-amd64/Packages
pigsty/dists/trixie/main/binary-amd64/Packages.gz
pigsty/dists/trixie/main/binary-arm64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
pigsty/dists/trixie/main/binary-arm64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
pigsty/dists/trixie/main/binary-arm64/Packages
pigsty/dists/trixie/main/binary-arm64/Packages.gz
```

An empty repository is still a complete one: empty `Packages` files, their gzip counterparts,
`by-hash` copies of both, and a `Release` at the Dist root. `apt update` succeeds against this
before you have added a single package.

The component is always `main`. APT requires one; SOW does not model more, so there is no
component parameter to get wrong.

## Step 2: Add packages

```bash
sow add ~/packages/deb -d trixie
```

```console
add repository=pigsty operation=1500549235801273162 accepted=8 failed=0 memberships=+8/-0 revision=6 generation=6 dirty=false
item input="/home/you/packages/deb/agentsview_0.37.5-1_amd64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:amd64" sha256:9f489369bbff02cde4b09397b91bbf367429d8e8cd9d97fc75ba5ea79bb9225a dists=trixie:accepted
item input="/home/you/packages/deb/agentsview_0.37.5-1_arm64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:arm64" sha256:164fbda74eb82cedacc42902387aa0552c72286dc9e8daa964f2f09e356b3324 dists=trixie:accepted
item input="/home/you/packages/deb/blackbox-exporter_0.28.0_amd64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:amd64" sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120 dists=trixie:accepted
item input="/home/you/packages/deb/blackbox-exporter_0.28.0_arm64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:arm64" sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3 dists=trixie:accepted
item input="/home/you/packages/deb/caddy_2.11.4-1_amd64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:amd64" sha256:79de4b2dda79161164b9b437a0f6d4339c1236f806e5750e8e488fa1e0ede679 dists=trixie:accepted
item input="/home/you/packages/deb/caddy_2.11.4-1_arm64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:arm64" sha256:3a21855bb702ffaaafa30f2b626808b43e220ea26cf53ed2ea5aabed0f1aa1dc dists=trixie:accepted
item input="/home/you/packages/deb/libpq5_18.4-1.pgdg24.04+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.4-1.pgdg24.04+1:arm64" sha256:923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21 dists=trixie:accepted
item input="/home/you/packages/deb/postgresql-client-common_291.pgdg24.04+1_all.deb" status=accepted format=deb coordinate="postgresql-client-common=291.pgdg24.04+1:all" sha256:8cae086c805e44272004d111f9f1177789dc14f0bcd07fd901471915a4eed001 dists=trixie:accepted
```

The DEB coordinate is `name=version:architecture` — for example
`libpq5=18.4-1.pgdg24.04+1:arm64`. The version is a full Debian version including epoch and
revision, compared with Debian's own rules everywhere SOW needs an ordering.

Everything came from the `control` file inside the archive, not the filename. Rename a `.deb`
however you like; the index still describes what is actually inside.

## Step 3: Read the pool layout

```bash
find pigsty/pool -name "*.deb" | sort
```

```console
pigsty/pool/a/agentsview/agentsview_0.37.5-1_amd64.deb
pigsty/pool/a/agentsview/agentsview_0.37.5-1_arm64.deb
pigsty/pool/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pigsty/pool/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pigsty/pool/c/caddy/caddy_2.11.4-1_amd64.deb
pigsty/pool/c/caddy/caddy_2.11.4-1_arm64.deb
pigsty/pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pigsty/pool/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

The path is `pool/<prefix>/<source>/<filename>`. Grouping is by **source package**, not binary
name, which is why `libpq5` lives under `postgresql-18` and `postgresql-client-common` lives
under `postgresql-common` — those are the `Source:` fields in their control files. A package
with no `Source:` field falls back to its binary name. The prefix follows the Debian rule: the
first character of the source name, or the first four characters when the source name starts
with `lib`.

This is the same grouping reprepro produces. The one difference is that SOW has no component
level in the pool: `pool/p/postgresql-18/` where reprepro writes
`pool/main/p/postgresql-18/`. See [Migration](/docs/tutorial/migration/) for a side-by-side.

## Step 4: Read the index layout

```bash
find pigsty/dists/trixie -type f | grep -v by-hash | sort
```

```console
pigsty/dists/trixie/main/binary-amd64/Packages
pigsty/dists/trixie/main/binary-amd64/Packages.gz
pigsty/dists/trixie/main/binary-arm64/Packages
pigsty/dists/trixie/main/binary-arm64/Packages.gz
pigsty/dists/trixie/Release
```

Check how the `all` package was projected:

```bash
for a in amd64 arm64; do
  echo "-- binary-$a"
  grep -E "^(Package|Architecture):" pigsty/dists/trixie/main/binary-$a/Packages | paste - -
done
```

```console
-- binary-amd64
Package: agentsview	Architecture: amd64
Package: blackbox-exporter	Architecture: amd64
Package: caddy	Architecture: amd64
Package: postgresql-client-common	Architecture: all
-- binary-arm64
Package: agentsview	Architecture: arm64
Package: blackbox-exporter	Architecture: arm64
Package: caddy	Architecture: arm64
Package: libpq5	Architecture: arm64
Package: postgresql-client-common	Architecture: all
```

`postgresql-client-common` is `Architecture: all`, so it appears in both indexes from a single
pool object and a single membership. `libpq5` is `arm64`-only, so it appears only in
`binary-arm64` — SOW does not invent an `amd64` entry for a package you did not provide.

### A Packages stanza

```bash
awk 'BEGIN{RS="";ORS="\n\n"} /^Package: libpq5/' pigsty/dists/trixie/main/binary-arm64/Packages
```

```console
Package: libpq5
Source: postgresql-18
Version: 18.4-1.pgdg24.04+1
Architecture: arm64
Maintainer: Debian PostgreSQL Maintainers <team+postgresql@tracker.debian.org>
Installed-Size: 1244
Depends: libc6 (>= 2.38), libgssapi-krb5-2 (>= 1.17), libldap2 (>= 2.6.2), libssl3t64 (>= 3.0.0)
Recommends: ca-certificates
Suggests: libpq-oauth
Section: libs
Priority: optional
Multi-Arch: same
Homepage: http://www.postgresql.org/
Description: PostgreSQL C client library
 libpq is a C library that enables user programs to communicate with
 the PostgreSQL database server.  The server can be on another machine
 and accessed through TCP/IP.  This version of libpq is compatible
 with servers from PostgreSQL 8.2 or later.
 .
 This package contains the run-time library, needed by packages using
 libpq. SSL certificate validation (the sslrootcert=system connection
 option) requires the ca-certificates package.
 .
 PostgreSQL is an object-relational SQL database management system.
Filename: pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
```

`Filename` is relative to the archive root — the directory you point `apt` at — so the whole
`pool/` tree is shared by every Dist in the repository.

Two things are deliberately absent. There is no `MD5sum` and no `SHA1`: every APT version that
still receives security updates verifies SHA-256, and publishing weak digests only invites
someone to trust them. And fields the package does not declare are omitted rather than emitted
empty — a package without a `Section:` has no `Section:` line.

## Step 5: Read the Release file

```bash
cat pigsty/dists/trixie/Release
```

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:20:50 UTC
X-SOW-Generation: 6
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 c602557313a6b3e2d63768e136a665e27896f25c72d575721b7285a8f36bae38 2719 main/binary-amd64/Packages
 c4010af6637fe4cfb2ce83353c5083201db2babb2d2310960c81d33c5f8ff3d6 1274 main/binary-amd64/Packages.gz
 26e85b720b8f3482a7145322dd218232943e5535064e56c30279cace799bd931 3846 main/binary-arm64/Packages
 5814f56db24ef5c8ebd67061d64b26d581a09611437c634403e0c51ea4a952b6 1687 main/binary-arm64/Packages.gz
```

`Acquire-By-Hash: yes` is the interesting line. It tells APT to fetch indexes by their content
hash instead of by name:

```bash
ls pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/
```

```console
10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
c4010af6637fe4cfb2ce83353c5083201db2babb2d2310960c81d33c5f8ff3d6
c602557313a6b3e2d63768e136a665e27896f25c72d575721b7285a8f36bae38
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Without `by-hash`, a client that reads `Release` just before you rebuild and fetches `Packages`
just after gets a hash mismatch and a failed `apt update`. With it, the client asks for the exact
bytes named in the `Release` it already read, and those bytes are still there — SOW keeps the
previous generation's index copies alongside the current one and deletes them only after the new
`Release` is in place. This is the single largest operational difference from reprepro, which
does not support `by-hash` at all.

`X-SOW-Generation` records which build produced this tree. It is informational; APT ignores
unknown fields.

## Step 6: Query what is in there

```bash
sow show 'deb:libpq5=18.4-1.pgdg24.04+1:arm64'
```

```console
{"repository":"pigsty","package":{"sha256":"923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21","format":"deb","coordinate":"libpq5=18.4-1.pgdg24.04+1:arm64","architecture":"arm64","canonical_arch":"aarch64","pool_path":"pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb","filename":"libpq5_18.4-1.pgdg24.04+1_arm64.deb","size":248592,"name":"libpq5","source":"postgresql-18","version":"18.4-1.pgdg24.04+1","kind":"main","storage":"pool","created_revision":6,"dists":["trixie"],"built_dists":["trixie"]}}
```

Both spellings of the architecture are reported: `architecture` is what the ecosystem calls it,
`canonical_arch` is the CPU family SOW stores.

A bare package name works when it is unambiguous, and refuses when it is not:

```bash
sow where blackbox-exporter
```

```console
operation rejected: managed: operation rejected: package reference "blackbox-exporter" is ambiguous: deb:blackbox-exporter=0.28.0:amd64 sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120, deb:blackbox-exporter=0.28.0:arm64 sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3
```

Exit code `6`. The candidates are printed in a form you can paste straight back. The full
grammar — `sha256:`, `rpm:`, `deb:`, filename, bare name — is in
[Package References](/docs/reference/package-ref/).

Once a repository has more than one Dist, commands that operate on packages need to know which
one you mean:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

Exit code `2`. Pass `-d trixie`.

## Step 7: Preview a removal before doing it

`sow rm -c` computes the entire consequence without taking a write lock or touching a byte:

```bash
sow rm caddy -d trixie --check | jq -r '.removed[] | "\(.dist)\t\(.coordinate)"'
```

```console
trixie	deb:caddy=2.11.4-1:amd64
trixie	deb:caddy=2.11.4-1:arm64
```

A bare name in `rm` means every version and native architecture of that name in the selected
Dist — here both `caddy` builds. The same output also carries the file-level plan:

```bash
sow rm caddy -d trixie --check | jq -r '.changes[] | "\(.op)\t\(.phase)\t\(.path)"'
```

```console
update	metadata	dists/trixie/main/binary-amd64/Packages
update	metadata	dists/trixie/main/binary-amd64/Packages.gz
add	metadata	dists/trixie/main/binary-amd64/by-hash/SHA256/260b4313742e5424c63235f568e9908701c2b6b3ab5e98d90120fa3194d8c670
add	metadata	dists/trixie/main/binary-amd64/by-hash/SHA256/c2e4559dc175b66bc6d52784e0d272bcc53596ea5372c62f15dc21a0312046f8
update	metadata	dists/trixie/main/binary-arm64/Packages
update	metadata	dists/trixie/main/binary-arm64/Packages.gz
add	metadata	dists/trixie/main/binary-arm64/by-hash/SHA256/a5ed9c07a26c462117fa6296faec08c34b52dcfa4730c2f689a2776260bdef4d
add	metadata	dists/trixie/main/binary-arm64/by-hash/SHA256/d2a892918009a7f6e7b81cb63ad89bee9523c4fade05d8535d0070ac6bd3f9a9
update	pointer	dists/trixie/Release
delete	delete	dists/trixie/main/binary-amd64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
delete	delete	dists/trixie/main/binary-amd64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
delete	delete	dists/trixie/main/binary-arm64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
delete	delete	dists/trixie/main/binary-arm64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Read the `phase` column top to bottom — it is the order the files actually change: new indexes
and their `by-hash` copies land first, the `Release` pointer flips second, and stale `by-hash`
entries are deleted last. A client mid-`apt update` can always finish with the `Release` it
started from.

Notice what is not in the plan: nothing under `pool/`. Removing membership does not delete
package bytes. Drop `--check` to execute.

## Step 8: Configure the APT client

Publish `~/repo/pigsty/` over HTTP — see [Serve Repositories](/docs/tutorial/serving/). Assume it
is at `https://repo.example.com/pigsty/`.

The archive root is the repository directory, and the suite is the Dist name. APT works out the
architecture directory itself.

{{< tabpane persist="header" >}}
{{< tab header="deb822 (Debian 12+, Ubuntu 22.04+)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /etc/apt/keyrings/pigsty.asc
{{< /tab >}}
{{< tab header="deb822 (unsigned, testing only)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Trusted: yes
{{< /tab >}}
{{< tab header="Legacy sources.list" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [arch=amd64 signed-by=/etc/apt/keyrings/pigsty.asc] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< tab header="Legacy (unsigned, testing only)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [arch=amd64 trusted=yes] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< /tabpane >}}

Prefer deb822 where it is available: it is the format Debian and Ubuntu are moving to, one field
per line, and it does not need the bracket syntax that people get wrong.

The `Trusted: yes` and `trusted=yes` variants disable signature verification entirely. Use them
to get the plumbing working, then follow [Sign Your Repository](/docs/tutorial/signing/) and
switch to `Signed-By`. That tutorial covers generating the key, publishing the armored public
half, and where to put it under `/etc/apt/keyrings/`.

Drop `Architectures:` / `arch=` if the client should fetch every architecture you publish.

## Step 9: Verify from a client

```bash
sudo apt update
apt-cache policy libpq5
sudo apt install -y blackbox-exporter
```

If `apt update` prints `Get:… Packages` lines and no hash or signature complaints, the `Release`
and both indexes parsed. `apt-cache policy` showing your repository as a candidate source means
`Filename` resolved.

This has been verified against Debian 13 with apt 3.0.3 and Debian 12 with apt 2.6.1, including
`InRelease` signature verification. Server logs confirm both fetch indexes through
`by-hash/SHA256/<hash>` rather than by name. The full matrix is in
[Compatibility](/docs/reference/compatibility/).

{{% alert title="by-hash needs a recent client" color="info" %}}
`Acquire-By-Hash` is understood by APT 1.2 and later, which covers every Debian and Ubuntu
release still supported. Older clients ignore the field and fetch `Packages` by name — that
still works, they just lose the protection against fetching across a rebuild.
{{% /alert %}}

## Where to go next

{{< doc-cards cols="2" >}}
{{< doc-card title="Sign Your Repository" link="/docs/tutorial/signing/" >}}
Generate a key, produce `InRelease` and `Release.gpg`, and switch clients to `Signed-By`.
{{< /doc-card >}}
{{< doc-card title="Serve Repositories" link="/docs/tutorial/serving/" >}}
A tested Nginx configuration, plus copying the tree to an air-gapped host.
{{< /doc-card >}}
{{< doc-card title="Build a YUM Repository" link="/docs/tutorial/yum-repo/" >}}
The RPM half of the same repository, including architecture views and policy.
{{< /doc-card >}}
{{< doc-card title="Migrate from reprepro" link="/docs/tutorial/migration/" >}}
Move an existing reprepro archive into a workspace, with a real layout comparison.
{{< /doc-card >}}
{{< /doc-cards >}}

For the complete directory tree including `by-hash` and pool grouping rules, see
[Repository Layout](/docs/reference/layout/). For every `sow.yml` field, see
[sow.yml Reference](/docs/reference/config/).
