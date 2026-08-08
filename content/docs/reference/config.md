---
title: "sow.yml Reference"
linkTitle: "Configuration"
description: "Every field of the workspace configuration file, with validation rules and a complete worked example."
url: "/docs/reference/config/"
weight: 200
icon: fa-solid fa-file-code
---

`sow.yml` is the single configuration file of a managed workspace. It sits at the
workspace root, declares which repositories and distributions exist, and holds the
membership policy and signing settings that every build applies. Plain mode
(`sow create`) never reads it.

This page lists every field the parser accepts. Anything not listed here is rejected —
there are no undocumented keys and no keys reserved for future use.

## How the file is read

SOW parses `sow.yml` with a strict decoder. Practically, that means:

- **Unknown fields are errors, not warnings.** A typo like `repositories:` instead of
  `repos:` fails the command with exit code `2` and names the offending line.
- **Exactly one YAML document.** A `---` separator introducing a second document is an
  error.
- **Regular file only.** A symlink at `sow.yml`, or a file larger than 16 MiB, is
  rejected before parsing.
- **Defaults are filled in at parse time,** not written back to disk. Run
  `sow config show --all` to see the fully expanded form.

Some of the file is machine-maintained. `sow init`, `sow repo new`, `sow repo rm`,
`sow dist new`, and `sow dist rm` rewrite `sow.yml` atomically as part of their
transaction. Membership policy and signing are yours to edit by hand; there are no CLI
flags that set them.

After any hand edit, run `sow config check`. It parses the file, cross-checks it against
the SQLite state of every initialized repository, and resolves every signing key
reference — without writing anything.

```bash
sow config check
```

```console
configuration valid: /srv/repo repositories=1 dists=2
```

## Top level

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  <name>: <repository>
targets:
  <name>: <publication-target>
```

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `schema` | string | yes | — | Must be exactly `sow/v3`. Any other value is a configuration error. |
| `architectures` | list of strings | no | `[x86_64, aarch64]` | The CPU families this workspace is allowed to manage. |
| `repos` | map | no | empty | Repository name to repository configuration. |
| `targets` | map | no | empty | Publication target name to target configuration. |

The v0.2.0 configuration value is exactly `schema: sow/v3`.

### architectures

This is a *ceiling*, not a target. It declares which architectures SOW may accept at all;
individual distributions inherit the whole list unless they narrow it.

Only two canonical families are supported today: `x86_64` and `aarch64`. The DEB
ecosystem names are accepted as input aliases and normalized at the parse boundary:

| You may write | Stored and displayed as |
|---|---|
| `x86_64`, `amd64` | `x86_64` |
| `aarch64`, `arm64` | `aarch64` |

So `architectures: [amd64, arm64]` and `architectures: [x86_64, aarch64]` are the same
configuration. Writing both aliases of one family — `[amd64, x86_64]` — is a duplicate and
fails:

```console
configuration error: load config "/srv/repo/sow.yml": workspace architectures: duplicate architecture "x86_64" after normalization
```

`noarch` (RPM) and `all` (DEB) are **not** architectures here. They are neutral packages,
projected into every applicable view at build time, and the parser rejects them in this
list. An unsupported value such as `riscv64` fails immediately:

```console
configuration error: load config "/srv/repo/sow.yml": workspace architectures: unsupported architecture "riscv64"; supported canonical families are x86_64 and aarch64
```

The list may be present or absent, but it may not be empty.

## Repository

```yaml
repos:
  pigsty:
    protected: true
    signing: { ... }
    dists: { ... }
```

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `protected` | bool | no | `false` | When true, `sow repo rm` refuses to delete this repository, even with `-f`. |
| `signing` | map | no | none | Package and metadata signing settings, see [Signing](#signing). |
| `dists` | map | no | empty | Distribution name to distribution configuration. |

### protected

`protected: true` is a guard against deleting a whole repository by accident. It blocks
exactly one thing — repository removal:

```console
operation rejected: managed: operation rejected: repository "pigsty" is protected
```

That is exit code `6`. Everything else keeps working normally: you can still `add`, `rm`,
`build`, create and delete distributions. To actually remove a protected repository, edit
`sow.yml` to set `protected: false`, confirm with `sow config check`, then run
`sow repo rm`.

### Repository names

Repository and distribution names share one grammar: they must match
`[a-z0-9][a-z0-9._-]*` — lowercase letters, digits, dot, underscore, hyphen, starting
with a letter or digit. Uppercase is rejected, because the name becomes a directory and
must behave identically on case-sensitive Linux and case-insensitive macOS filesystems.

```console
configuration error: load config "/srv/repo/sow.yml": repository name "Infra": name "Infra" must match [a-z0-9][a-z0-9._-]*
```

These names are reserved and rejected: `.`, `..`, `.sow`, `pool`, `dists`, `sow.yml`,
`workspace.lock`, `workspace-ops`, `repo-locks`. Two repository names that would collide
in the state directory — say `db` and `db.db` — are also rejected:

```console
configuration error: load config "/srv/repo/sow.yml": repository names "db" and "db.db" collide at reserved state path "db.db"
```

See
[Repository Layout](/docs/reference/layout/) for why.

## Dist

```yaml
    dists:
      el9:
        format: rpm
        architectures: [x86_64]
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]
```

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `format` | string | yes | — | `rpm` or `deb`. A distribution holds exactly one format. |
| `architectures` | list of strings | no | inherits workspace list | Narrows this distribution to a subset of the workspace families. |
| `limit` | integer | no | `0` | Maximum versions to keep per package name and architecture; `0` keeps all. |
| `exclude` | list of rules | no | empty | Rules that keep matching packages out of this distribution. |

### format

`format` is the only field `sow dist new` sets from the command line, and it cannot be
changed afterwards — an RPM distribution never becomes a DEB one. A package whose format
does not match is simply not a candidate for that distribution.

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" format must be rpm or deb, got "apk"
```

### architectures

Omit this field and the distribution inherits the workspace list, which is what you want
almost always. Declare it only to narrow: an `el9` distribution that should be x86-only
in an otherwise dual-architecture workspace.

The list must be a subset of the workspace list, and it may not be empty:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" architecture "aarch64" is not allowed by workspace
```

Adding a family here marks the distribution dirty; the next `sow build` renders the new
view. Removing a family that is still referenced by existing membership or by the built
generation is refused by `config check` and by every write command.

### limit

`limit` caps how many versions of one package survive in this distribution. The grouping
key is `(binary name, native architecture)`, so an x86_64 build and an aarch64 build of
the same package are counted separately, and a `noarch`/`all` package forms its own group.

- `0` (the default) keeps every version.
- `N > 0` keeps the newest `N`, comparing RPM EVR or Debian version with the native
  ordering rules of each ecosystem.
- A negative value is a configuration error.

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: limit must be zero or positive, got -1
```

With `limit: 1`, adding an older version alongside a newer one reports it as limited and
does not create membership:

```console
item input=".../libpq5_18.2-1.pgdg12+1_amd64.deb" status=excluded format=deb coordinate="libpq5=18.2-1.pgdg12+1:amd64" sha256:310611d0... dists=trixie:limited
item input=".../libpq5_18.3-1.pgdg12+1_amd64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:amd64" sha256:4b526223... dists=trixie:accepted
```

Raising `limit` later does not resurrect versions that policy previously removed. The
package bytes may still sit in the pool, but membership is gone; re-add the file to bring
it back. See [Membership Policy](/docs/feature/policy/) for the reasoning.

### exclude

`exclude` is a list of rules. Each rule is a set of fields; within a rule the fields are
ANDed, within a field the patterns are ORed, and rules are ORed with each other. A package
is excluded if any single rule matches it.

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

That reads: drop every debug-flavored package, and separately drop aarch64 packages whose
name starts with `test-` or ends with `-experimental`.

Five fields are allowed:

| Field | Matched against |
|---|---|
| `name` | Binary package name |
| `source` | Normalized source name (RPM `SOURCERPM`, DEB `Source`) |
| `arch` | `x86_64`, `aarch64`, or `neutral` |
| `kind` | The classification below |
| `format` | `rpm` or `deb` |

`kind` is derived from the binary package name by its most specific suffix:

| Format | Name suffix | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| any | none of the above | `main` |

Patterns are case-sensitive: either an exact string or a shell glob using `*`, `?`, and
`[...]`. There is no regex, no version comparison, no negation, and no expression syntax.
An empty rule, an empty or untrimmed pattern, a repeated pattern within one field, and an
invalid glob are all configuration errors:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: exclude rule 0 is empty
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: exclude rule 0 field name has invalid glob "[bad": syntax error in pattern
```

Policy order is fixed: `exclude` runs first, then `limit`. An excluded package is reported
per item and is not a failure:

```console
item input=".../blackbox_exporter-0.28.0-1.x86_64.rpm" status=excluded format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643... dists=el9:excluded
```

## Signing

Signing settings live on the repository, not on individual distributions, and cover two
independent trust chains: the packages themselves, and the repository metadata clients
verify before they trust anything else.

```yaml
    signing:
      rpm:
        packages:
          mode: fill
          key: env://SOW_RPM_PACKAGE_KEY
          trusted_keys: [keys/pgdg.asc]
        metadata:
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
      deb:
        metadata:
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
```

The tree is fixed. `signing.rpm` has `packages` and `metadata`; `signing.deb` has
`metadata` only — DEB packages are never re-signed, because APT verifies the archive
through `Release`, not through per-package signatures.

### rpm.packages

| Field | Type | Default | Meaning |
|---|---|---|---|
| `mode` | string | `never`, or `fill` when `key` is set | `never`, `fill`, or `always`. |
| `key` | key reference | none | The signing key. Required unless `mode` is `never`. |
| `trusted_keys` | list of key references | empty | Additional public keys accepted by `fill`. |

The three modes:

- **`never`** — input bytes are stored verbatim. Whatever signature the package arrived
  with (including none) is what clients get.
- **`fill`** — sign packages that have no signature, or whose signature is not verifiable
  by `key` or one of `trusted_keys`. Packages that already verify keep their exact bytes.
- **`always`** — every package must end up signed by `key`. Packages already signed by it
  keep their bytes; everything else is re-signed.

`fill` is the default when a key is present, because it is the mode that preserves
upstream signatures. Setting `mode` to `fill` or `always` without a key is an error:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: rpm packages mode "fill" requires key
```

`trusted_keys` is a list of public keys whose signatures `fill` accepts as already-good.
The public half of `key` is always trusted and does not need to be listed. Repeating the
same reference twice is an error:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: duplicate rpm trusted key reference "keys/x.asc"
```

RPM package signing is the one operation that shells out: SOW calls the environment's
`rpm --addsign` / `rpm --resign` against a private staged copy, never against your input
file. The private key must be available to the GPG environment that `rpm` uses.

### rpm.metadata and deb.metadata

| Field | Type | Default | Meaning |
|---|---|---|---|
| `key` | key reference | none | Key used to sign repository metadata. |
| `passphrase` | passphrase reference | none | Passphrase for a protected private key. |

Configure `rpm.metadata.key` and every RPM architecture view additionally publishes a
detached `repodata/repomd.xml.asc`. Configure `deb.metadata.key` and every DEB
distribution additionally publishes a clearsigned `InRelease` and a detached
`Release.gpg`. Without a key, those files are simply not produced — `repomd.xml` and
`Release` are always written.

For `file://` and `env://` references SOW signs in-process; no `gpg` binary is involved.
Only `agent://` requires `gpg` in the environment.

Changing a key reference or the fingerprint behind it marks the affected distributions
dirty, because the signing identity is part of each distribution's built configuration
digest. The next `sow build` re-signs and produces a new generation.

### Key references

A key reference is a string in one of these forms:

| Form | Example | Notes |
|---|---|---|
| Path | `keys/repo-signing.asc` | ASCII-armored key file. A relative path resolves against the workspace root, not your current directory. |
| `file://<path>` | `file:///secure/repo-signing.asc` | Same as above, written explicitly. Absolute paths therefore show three slashes. |
| `env://<VAR>` | `env://SOW_METADATA_KEY` | The variable holds the armored key material itself, not a path. The name must match `[A-Za-z_][A-Za-z0-9_]*`. |
| `agent://<fingerprint>` | `agent://7F721C4AD40F...CF3B` | Delegates to the ambient `gpg-agent`. The fingerprint is 16, 40, or 64 hex digits, case-insensitive. |

Any other scheme is rejected:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: deb metadata key: unsupported key reference scheme in "https://example.com/key.asc"
```

References are validated in two stages. Syntax is checked when the file is parsed and
fails with exit code `2`. Whether the reference actually *resolves* is checked by
`sow config check` and by every write command, and fails with exit code `6`:

```console
operation rejected: ... deb metadata key: key reference does not resolve to a bounded regular file
operation rejected: ... deb metadata key: environment key reference SOW_METADATA_KEY is unset
operation rejected: ... deb metadata key: gpg public-key export returned no bounded key material
```

Secret material never leaves the reference. `sow config show --all` prints the reference
and the resolved fingerprint, and nothing else:

```yaml
    signing:
      deb:
        metadata:
          key: file:///srv/repo/keys/repo-signing.asc
          key_fingerprint: 7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
```

Private keys and passphrases are never written to `sow.yml`, SQLite, the operation log,
JSON output, or error messages.

### Passphrase references

`passphrase` accepts the same path, `file://`, and `env://` forms as a key reference —
but not `agent://`, since a passphrase is a value, not a key handle.

Two rules apply:

- A passphrase without a key is an error. It has nothing to unlock.

  ```console
  configuration error: ... repository "a" signing: deb metadata passphrase requires key
  ```

- A passphrase alongside an `agent://` key is an error. The agent owns the private key and
  handles its own prompting; a second passphrase channel would be ignored.

  ```console
  configuration error: ... repository "a" signing: rpm metadata agent key uses its ambient gpg-agent and cannot accept a passphrase reference
  ```

## Publication targets

Each target binds one configured Repository to a storage namespace. Target names use the
same lower-case name grammar as repositories.

```yaml
targets:
  local:
    repository: pigsty
    provider: filesystem
    endpoint: file:///srv/mirror
    prefix: pigsty
    public_endpoint: file:///srv/mirror/pigsty/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true

  prod:
    repository: pigsty
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: pigsty
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/pigsty/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

| Field | Required | Meaning |
|---|---|---|
| `repository` | yes | Existing Repository owned by this target. |
| `provider` | yes | `filesystem` or `r2`. |
| `endpoint` | yes | Canonical `file:///absolute/path` without trailing slash, or canonical `https://host` for R2. |
| `region` | R2 | Must be `auto`; forbidden for filesystem. |
| `bucket` | R2 | Lower-case canonical bucket name; forbidden for filesystem. |
| `prefix` | yes | Relative public-tree prefix; empty means the storage namespace root. |
| `credential` | R2 | `env://NAME` or `file:///absolute/path`; inline secrets are forbidden. |
| `public_endpoint` | yes | Canonical `https://`, `http://`, or `file://` URL ending in `/`, used for public-absence evidence. |
| `max_cache_ttl` | yes | Canonical non-negative Go duration, including explicit `0s`. |
| `authoritative_workspace` | yes | Must be `true`. |
| `single_writer` | yes | Must be `true`. |
| `exclusive_write_authority` | yes | Must be `true`. |

The three authority booleans are explicit safety acknowledgements, not defaults. Targets
on the same storage may not have overlapping prefixes; filesystem targets may not resolve
to overlapping effective paths. These rules protect conditional publication and GC from
competing writers.

For `provider: filesystem`, configuration validation checks URL shape and overlap. At
publication time the endpoint directory itself must already exist, must not be a symlink,
and must resolve to one canonical real directory. SOW creates the configured prefix below
that endpoint, not the endpoint itself.

R2 credentials are private references. The environment variable value or referenced file
must contain one strict JSON document, not a path or shell assignment:

```json
{"access_key_id":"R2_ACCESS_KEY_ID","secret_access_key":"R2_SECRET_ACCESS_KEY"}
```

An optional temporary credential may add `"session_token":"..."`. Unknown fields,
trailing data, missing access/secret values, and documents larger than 64 KiB are rejected.
`config show`, JSON output, and the public tree never contain the credential material.

## Complete example

A workspace with two repositories: a protected production repository signing both
metadata chains and filling in missing RPM signatures, and a scratch repository with no
signing and no policy.

```yaml
# sow.yml — workspace root configuration
schema: sow/v3

# CPU families this workspace may manage. This is a ceiling, not a target.
# amd64/arm64 are accepted as input aliases and normalized to x86_64/aarch64.
architectures: [x86_64, aarch64]

repos:

  # Production repository. Deleting it requires editing this file first.
  pigsty:
    protected: true

    signing:
      rpm:
        packages:
          # Sign RPMs that arrive unsigned or with an untrusted signature.
          # Packages already signed by a trusted key keep their exact bytes.
          mode: fill
          key: keys/package-signing.asc
          trusted_keys:
            - keys/pgdg.asc        # upstream PGDG signatures are accepted as-is
        metadata:
          # Publishes repodata/repomd.xml.asc next to every repomd.xml.
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
      deb:
        metadata:
          # Publishes InRelease and Release.gpg next to every Release.
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE

    dists:

      # Stable EL9 channel: one version per package, no debug artifacts.
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]

      # Beta channel: same packages, every version kept for rollback.
      el9-beta:
        format: rpm
        limit: 0
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]

      # Debian trixie, x86 only, newest version wins.
      trixie:
        format: deb
        architectures: [x86_64]
        limit: 1
        exclude:
          - kind: [dbgsym, dbg]
          - name: ["*-experimental"]

  # Scratch repository: unsigned, unfiltered, deletable.
  sandbox:
    dists:
      el9:
        format: rpm
      trixie:
        format: deb

targets:
  prod:
    repository: pigsty
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: pigsty
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/pigsty/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

Validate it before you rely on it:

```bash
sow config check
sow config show --all
```

## What is not in sow.yml

Some things you might expect to configure are deliberately not configurable:

- **Repository paths.** A repository always lives at `<workspace>/<name>`. There is no
  `path:` field. See [Repository Layout](/docs/reference/layout/).
- **APT components.** Always `main`. YUM has no component concept.
- **Architecture views.** Derived from `architectures` and the package headers, never
  declared per package.
- **Inline secrets.** Targets accept only credential references; key and passphrase material
  likewise stays behind a reference.
- **Automatic retention counts.** Retention is an explicit `sow retain add/rm` operation,
  not a rolling count in configuration.

## See also

- [`sow config`](/docs/reference/cli/config/) — the commands that read this file
- [Membership Policy](/docs/feature/policy/) — how `exclude` and `limit` behave over time
- [Signing Model](/docs/feature/signing/) — the two trust chains explained
- [Publish, Retain, GC, and Export](/docs/reference/cli/publication/) — target lifecycle commands
- [Exit Codes](/docs/reference/exit-codes/) — what `2` and `6` mean here
