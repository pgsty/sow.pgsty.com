---
title: "sow ls / show / where"
linkTitle: "ls / show / where"
description: "Three read-only queries: list a Dist's membership, inspect one package object, locate a package across the Workspace."
url: "/docs/reference/cli/query/"
weight: 800
icon: fa-solid fa-magnifying-glass
---

Three commands answer three different questions. `ls` lists what a Dist should contain, `show`
inspects one package object in detail, and `where` finds which Dists — in any Repository — carry a
package. All three are read-only, take no write lock, and share the same `--json` envelope.

## Synopsis

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

## Common options

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | selection rules |
| `--json` | Emit the versioned JSON envelope | false |

There is no `--pool`, no `--match`, and no per-command format flag.

## sow ls

Lists the Desired Membership of the selected Dists.

```console
sow ls -r pigsty -d el9
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16	rpm:centos-release-0:6-0.el6.centos.5.x86_64	el9	el9	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead	rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64	el9	el9	pool/c/centos-release/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab	rpm:epel-release-0:7-5.noarch	el9	el9	pool/e/epel-release/epel-release-7-5.noarch.rpm
```

The `SHA256` and `COORDINATE` columns are exact references you can paste straight into
[`sow rm`](/docs/reference/cli/rm/) or `sow show`.

### Desired versus Built

`DISTS` is Desired Membership; `BUILT_DISTS` is what the current Built Generation actually contains.
When the Repository is dirty, the header says so and the divergence is visible per row — an empty
`BUILT_DISTS` means clients cannot see that package yet:

```console
sow ls -r demo
repository=demo dists=el9 dirty=true
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16	rpm:centos-release-0:6-0.el6.centos.5.x86_64	el9		pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead	rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64	el9	el9	pool/c/centos-release/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
```

### Dist selection is mandatory

`ls` needs an unambiguous Dist set. In a multi-Dist Repository, either pass `-d` or run the command
from inside `<repo>/dists/<dist>/`:

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

An object that belongs to several Dists shows all of them, which is the quickest way to see
cross-Dist sharing:

```console
sow ls -r pgsql -d trixielim
repository=pgsql dists=trixielim dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c	deb:libpq5=18.3-1:amd64	trixie,trixielim	trixie,trixielim	pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c	deb:libpq5=18.3-1:arm64	trixie,trixielim	trixie,trixielim	pool/p/postgresql-18/libpq5_18.3-1_arm64.deb
sha256:f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3	deb:pg-sample=1.17-1:all	trixie,trixielim	trixie,trixielim	pool/p/pg-sample/pg-sample_1.17-1_all.deb
```

## sow show

Prints one Package Object in full: coordinate, content hash, normalized facts, pool path, signature
identity and membership. Because there is no compact tabular form, `show` prints JSON on stdout even
without `--json`.

```console
sow show 'rpm:epel-release-0:7-5.noarch' -r pigsty -d el9
{"repository":"pigsty","package":{"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","format":"rpm","coordinate":"epel-release-0:7-5.noarch","architecture":"noarch","canonical_arch":"neutral","pool_path":"pool/e/epel-release/epel-release-7-5.noarch.rpm","filename":"epel-release-7-5.noarch.rpm","size":14524,"name":"epel-release","source":"epel-release","version":"7","epoch":"0","release":"5","kind":"main","payload_sha256":"94b51b9827b4238f8aecbff8da45fa833998f8589c15316376d52201304e0136","signature_key":"24C6A8A7F4A80EB5","storage":"pool","created_revision":3,"dists":["el9"],"built_dists":["el9"]}}
```

Fields worth knowing:

| Field | Meaning |
|---|---|
| `canonical_arch` | `x86_64`, `aarch64`, or `neutral` for RPM `noarch` / DEB `all` |
| `kind` | Policy classification derived from the binary name: `main`, `debuginfo`, `debugsource`, `llvmjit`, `dbgsym`, `dbg` |
| `source` | Normalized source name — RPM `SOURCERPM`, DEB `Source`, falling back to the binary name |
| `payload_sha256` | RPM only: the signature-neutral digest used for re-signing idempotence |
| `signature_key` | Key ID of the embedded signature, when the package carries one |
| `storage` | `pool` once published; a pending object is still in the private store |

`show` searches the selected Repository by default. `-d` narrows the candidate set, it does not
change what identity means. With `--json` the same object arrives inside the standard envelope:

```console
sow show 'deb:pg-sample=1.17-1:all' -r pgsql -d trixie --json
{"schema":"sow.cli/v1","command":"show","ok":true,"repository":"pgsql","operation":null,"result":{"repository":"pgsql","package":{"sha256":"f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3","format":"deb","coordinate":"pg-sample=1.17-1:all","architecture":"all","canonical_arch":"neutral","pool_path":"pool/p/pg-sample/pg-sample_1.17-1_all.deb","filename":"pg-sample_1.17-1_all.deb","size":566,"name":"pg-sample","source":"pg-sample","version":"1.17-1","kind":"main","storage":"pool","created_revision":4,"dists":["trixie"],"built_dists":["trixie"]}},"errors":[]}
```

### Bare names must be unique for show

This is the one place `show` and `rm` differ. `rm foo` means "every version of foo"; `show foo`
means "the single object called foo" and fails with the candidate list when that is not true:

```console
sow show libpq5 -r pgsql -d trixie
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1:amd64 sha256:fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41, deb:libpq5=18.3-1:amd64 sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c, deb:libpq5=18.3-1:arm64 sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c
```

Copy one of the printed coordinates and re-run. The same rule applies to `where`.

## sow where

Locates a reference across the *whole* Workspace — every Repository, not just the selected one. It is
the answer to "which of my Dists is still shipping this".

```console
sow where epel-release
{"reference":"epel-release","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","coordinate":"rpm:epel-release-0:7-5.noarch"}]}
```

`-r` and `-d` narrow the search. With `--json`:

```console
sow where 'deb:libpq5=18.2-1:amd64' --json
{"schema":"sow.cli/v1","command":"where","ok":true,"repository":null,"operation":null,"result":{"reference":"deb:libpq5=18.2-1:amd64","locations":[{"repository":"pigsty","dists":["trixie"],"built_dists":["trixie"],"sha256":"fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41","coordinate":"deb:libpq5=18.2-1:amd64"}]},"errors":[]}
```

Not finding anything is a rejection, so the command is usable as a gate in a script:

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## Reference grammar

`show` and `where` accept the same references as `rm`: `sha256:<hex>`, `rpm:<NEVRA>`,
`deb:<name>=<version>:<arch>`, a full filename, or a bare binary name. A NEVRA without the `rpm:`
prefix does not match. See [Package References](/docs/reference/package-ref/) for the complete rules.

## Examples

Audit what a Dist will deliver, sorted by pool path:

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[].pool_path' | sort
```

Find every package still waiting for a build:

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[] | select(.built_dists | length == 0) | .coordinate'
```

Check whether a CVE-affected build is still published anywhere:

```bash
sow where 'rpm:patroni-0:3.0.4-1.noarch' --json | jq -r '.result.locations[] | "\(.repository)/\(.dists|join(","))"'
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Result printed, including an empty membership list |
| `1` | Runtime I/O error reading state |
| `2` | Usage error, Workspace not found, or an ambiguous Repository/Dist selection |
| `5` | The state database could not be read or parsed |
| `6` | Reference matched nothing, or a bare name matched several objects |

## See also

- [Package References](/docs/reference/package-ref/) — the five reference forms and disambiguation
- [sow rm](/docs/reference/cli/rm/) — where the references from `ls` are usually used
- [sow status / check](/docs/reference/cli/build/) — Repository-level state instead of per-package
- [Pool & Architecture Views](/docs/feature/views/) — how `pool_path` maps into client-visible views
- [JSON Output](/docs/reference/json/) — full result schemas
