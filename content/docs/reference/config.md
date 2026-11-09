---
title: "sow.yml Reference"
linkTitle: "Configuration"
description: "Workspace fields, defaults, validation rules, signing references, and publication targets."
categories: [Reference]
tags: [config, managed]
url: "/docs/reference/config/"
weight: 200
icon: fa-solid fa-file-code
---

`sow.yml` configures a Managed workspace. It declares repositories, Dists, package policy,
signing, and publication targets. Plain `sow create` does not read it.

After editing the file, validate it and inspect the effective settings:

```bash
sow config check
sow config show --all
```

`config check` validates the YAML, compares it with initialized repository state, and
resolves signing references. `--all` expands defaults in `config show`.

<span id="how-the-file-is-read" data-td-print-local></span>

## File rules

- Use one YAML document and `schema: sow/v3`.
- Unknown fields and duplicate keys are errors.
- Keep the file at the workspace root as a regular file with one hard link, at most 16 MiB.
  A symlink is rejected.
- `init`, `repo new/rm`, and `dist new/rm` update the file as part of their operations.
- Edit policy, signing, and target settings in the file. Defaults are applied when read;
  reading does not rewrite the source.

Use [`repo migrate`](/docs/command/repo/#sow-repo-migrate) to upgrade an older repository database or layout.

<span id="top-level" data-td-print-local></span>
<span id="architectures" data-td-print-local></span>
<span id="complete-example" data-td-print-local></span>

## Workspace

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos: {}
targets: {}
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `schema` | string | Required | Must be `sow/v3` |
| `architectures` | string list | `[x86_64, aarch64]` | Architecture families allowed in this workspace |
| `repos` | map | Empty | Repository names and settings |
| `targets` | map | Empty | Publication target names and settings |

Architecture aliases normalize as follows:

| Input | Canonical family |
|---|---|
| `x86_64`, `amd64` | `x86_64` |
| `aarch64`, `arm64` | `aarch64` |

A specified architecture list must not be empty or contain duplicate families after
normalization. `noarch` and `all` are package architectures, not configuration families.
SOW includes those neutral packages in each applicable view.

<span id="protected" data-td-print-local></span>
<span id="repository-names" data-td-print-local></span>

## Repository

```yaml
repos:
  demo:
    protected: false
    signing: {}
    dists:
      el9:
        format: rpm
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `protected` | boolean | `false` | Blocks `repo rm`, including `-f` |
| `signing` | map | Unsigned metadata; package mode `never` | Repository signing settings |
| `dists` | map | Empty | Dist names and settings |

`protected` does not block package changes or Dist removal. To remove a protected
repository, set it to `false`, validate the configuration, then run `repo rm`.

Repository, Dist, and target names must match `[a-z0-9][a-z0-9._-]*`.
Reserved names are `.`, `..`, `.sow`, `pool`, `dists`, `sow.yml`, `workspace.lock`,
`workspace-ops`, and `repo-locks`. Repository names must also have distinct private state
paths; for example, `db` and `db.db` cannot coexist.

<span id="format" data-td-print-local></span>
<span id="architectures-1" data-td-print-local></span>
<span id="limit" data-td-print-local></span>

## Dist

```yaml
dists:
  el9:
    format: rpm
    architectures: [x86_64]
    limit: 2
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `format` | string | Required | `rpm` or `deb`; cannot change after initialization |
| `architectures` | string list | Workspace list | A nonempty subset of workspace families |
| `limit` | integer | `0` | Newest versions to keep per binary name and canonical architecture; `0` keeps all |
| `exclude` | rule list | Empty | Package exclusion rules |
{.wide .expand}

Adding an architecture makes the Dist dirty; run `build` to generate its view.
Removing an architecture still referenced by membership or built state is rejected.

`limit` must be non-negative. RPM uses epoch-version-release ordering; DEB uses Debian
version ordering. Neutral packages form a separate group. Relaxing policy does not
restore removed members; add their package files again.

<span id="exclude" data-td-print-local></span>

### Exclusion rules

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

Fields within one rule use AND. Patterns within one field use OR. Rules use OR.
`exclude` runs before `limit` over the complete candidate membership of each selected Dist.

| Field | Matches |
|---|---|
| `name` | Binary package name |
| `source` | Normalized RPM `SOURCERPM` or DEB `Source` name |
| `arch` | `x86_64`, `aarch64`, or `neutral` |
| `kind` | RPM: `debuginfo`, `debugsource`, `llvmjit`; DEB: `dbgsym`, `dbg`; otherwise `main` |
| `format` | `rpm` or `deb` |

Patterns are case-sensitive strings or shell globs (`*`, `?`, `[...]`). Empty rules,
empty or untrimmed patterns, duplicates within one field, and invalid globs are errors.
Pattern values are not checked against the possible package values; a typo can match
nothing. `kind` comes from the corresponding package-name suffix.

See [Membership policy](/docs/feature/policy/) for examples and result interpretation.

## Signing

Signing applies to a repository. RPM packages, RPM metadata, and DEB metadata have
separate settings:

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      passfile: /run/secrets/rpm-password
      trusted_keys: [keys/upstream.asc]
    metadata:
      key: keys/repo-signing.asc
      passfile: /run/secrets/metadata-password
  deb:
    metadata:
      key: keys/repo-signing.asc
      passfile: /run/secrets/metadata-password
```

<span id="rpmpackages" data-td-print-local></span>

### RPM package settings

| `rpm.packages` field | Default | Meaning |
|---|---|---|
| `mode` | `never` without a key; `fill` with a key | `never`, `fill`, or `always` |
| `key` | None | Signing-key reference; required for `fill` and `always` |
| `passfile` | None | Password-file path; requires `key` |
| `trusted_keys` | Empty | Additional public-key references accepted by `fill` |
{.wide .expand}

`never` preserves input bytes. `fill` preserves packages whose signatures verify with
the current or trusted keys and signs the rest. `always` requires the current key,
re-signing packages when needed. The public half of `key` is trusted automatically.
Duplicate trusted-key reference strings are rejected.

Package signing calls the host `rpm` command on a staged copy. Its GPG environment must
already contain the private key. A configured key file alone does not provision it.

<span id="rpmmetadata-and-debmetadata" data-td-print-local></span>

### Metadata settings

Both `rpm.metadata` and `deb.metadata` accept:

| Field | Default | Meaning |
|---|---|---|
| `key` | None | Metadata signing-key reference |
| `passfile` | None | Password-file path; requires `key` |
| `passphrase` | None | Legacy password reference; mutually exclusive with `passfile` |

RPM signing creates `repodata/repomd.xml.asc`. DEB signing creates `InRelease` and
`Release.gpg`. Without a key, indexes are unsigned. DEB package files are not re-signed.

### Key references

| Form | Example | Value |
|---|---|---|
| Path | `keys/repo.asc` | OpenPGP key file; relative paths start at the workspace root |
| `file://` | `file:///secure/repo.asc` | OpenPGP key file |
| `env://` | `env://SOW_METADATA_KEY` | Variable containing armored key material, a file path, or a GPG key identifier |
| `agent://` | `agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B` | Key in the local GPG environment |
{.wide .expand}

Environment names use `[A-Za-z_][A-Za-z0-9_]*`. A GPG key identifier is a 16-digit key ID
or a 40- or 64-digit fingerprint. Hexadecimal letters are case-insensitive.

Key files accept ASCII-armored or binary OpenPGP data and must be regular files without
symlinks, at most 16 MiB. Relative paths resolve from the workspace root.
Metadata signing uses the supplied private-key material inside SOW. A GPG key identifier
uses external `gpg`, whether supplied through `agent://` or an environment variable.

A signing `key` reference must resolve to exactly one primary key.
A `trusted_keys` file can contain several complete public keys, including consecutive armored blocks.
SOW reads the complete bundle and rejects malformed or truncated input. It does not silently use only the first key.

### Password files {#passfile}

This interface requires SOW 0.7.0 or later. Check
`sow help create` or `sow help config check` for support in an installed binary.

Use one password-file interface for RPM packages, RPM metadata, and APT metadata,
including protected private-key files and `agent://` keys. The sources are selected
in this order, separately for each signing key:

1. `--passfile PATH`: override every signing key used by this invocation.
2. The key's configured `passfile`, or its legacy `passphrase` reference.
3. `SOW_GPG_PASSFILE`: default file path for keys without a configured source.
4. Existing key/GPG/RPM credential handling when no source is set.

Configure `passfile` next to `key` under `repos.<name>.signing.rpm.packages`,
`signing.rpm.metadata`, or `signing.deb.metadata`; it is not a top-level setting.
An empty YAML `passfile: ""` is treated as unset. A CLI override does not bypass
configuration validation: two nonempty `passfile` and `passphrase` values on the
same metadata key are still rejected.

`passfile` takes a literal filesystem path, not a URL or an environment-variable name.
CLI and environment paths are relative to the process working directory, even with
`-C`. Config paths are relative to the workspace root. SOW does not expand `~` or
`$VARIABLE` in config or environment values; the shell can expand them in CLI arguments.
No default file is searched. Set `SOW_GPG_PASSFILE` to an absolute path to reuse a source
across commands. An empty `SOW_GPG_PASSFILE` is an error if that source is selected
when credentials are needed; CLI or per-key configuration can override it. Unset
the variable to return to existing behavior.

Without a source, an encrypted metadata key file still needs a password reference.
External metadata GPG can use an already unlocked agent key but runs with pinentry
disabled; RPM retains its existing agent and macro behavior. An unprotected key
does not require a password file. The environment variable only supplies a password
source: Plain `create` still needs `--sign-with` to enable signing.

```bash
sow create ./packages -S 0123456789ABCDEF --passfile /run/secrets/gpg-password
export SOW_GPG_PASSFILE=/run/secrets/gpg-password
sow config check
sow build -r demo
```

The file contains the password itself, with these exact rules:

- One nonempty UTF-8 line, without a BOM, at most 64 KiB including an optional terminator.
- No final newline is required. Exactly one final LF or CRLF is removed.
- No trimming: leading/trailing spaces and tabs are password bytes. Quotes, `#`, and
  backslashes are literal; there are no comments, escapes, or `NAME=value` syntax.
- Empty files, an empty line, NUL, embedded CR/LF, a bare final CR, and extra blank
  lines are rejected. A password consisting only of spaces is not empty.
- Use a readable regular file with no symlinks in its path. FIFOs, directories, and
  stdin (`-`) are not special sources. macOS system aliases `/tmp`, `/var`, and `/etc`
  are normalized to their `/private` locations.

Keep the file outside the repository and public document root, normally with mode
`0600` and a private parent directory. SOW does not require exactly `0600`, so a
read-only secret mounted with suitable access controls also works. File paths do not
hide the password from processes or users that can read the file.

SOW reads the selected source only for signing or a signing preflight. A missing,
unreadable, or malformed selected source fails without trying another source or
opening a password prompt. With an explicit source, external GPG uses [batch loopback mode](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Esoteric-Options.html), which must be
allowed by the agent; hardware keys that require interaction retain that requirement.
No new raw-password flag or environment variable is provided.

The option is available on `create` (with `--sign-with`), `init`, `config check`,
`repo new/rm/migrate`, `dist new/rm`, `add`, `rm`, `build`, and `export rpm-leaf`.
`add --skip` can still sign packages; `rm --check` can render signed preview metadata.
`publish`, local/target `gc`, and `log prune` also accept it because recovery of an
interrupted mutation can need a signer. Query commands, `config show`, and signature
verification with `check` do not read password files. `retain` does not accept
`--passfile`. Recovery selects the source
again from the current invocation and configuration; password values are never journaled.

Changing only a `passfile` path does not change a signing identity or make a Dist dirty.
Password values never enter logs, config output, repository state, or public files.
External metadata signing passes the password through a private descriptor. RPM signing
uses a temporary `0600` file in a private `/tmp/sow-gpg-pass-*` directory because RPM
may invoke GPG repeatedly. SOW removes it when the signing call returns; forced process
termination can leave it behind.

### Passphrase references

Existing metadata `passphrase` fields remain supported, including paths, `file://`, and
`env://` references. They now also work with GPG key identifiers. They take priority over
`SOW_GPG_PASSFILE`; `--passfile` overrides them. Nonempty `passfile` and `passphrase`
values on one key are a configuration error. New configuration should use `passfile`.
Moving from `passphrase` to `passfile` can require one metadata rebuild, because
historical configuration identities include the legacy reference.

Legacy references keep their byte-oriented behavior: at most 64 KiB, nonempty, no NUL,
remove one final LF and then one final CR. In-process legacy keys retain support for
other bytes; external GPG requires a single line. Legacy file paths resolve from the
workspace root and use the same regular-file and no-symlink rules as keys.

For `config check`, reference syntax errors return `2`; unresolved or unusable
signing references return `6`. Metadata key files are unlocked and checked for
signing suitability; external GPG metadata keys also perform a signing probe.
RPM package checks validate the selected password file's format, the tools, and
secret-key availability. They do not sign a package or prove its password is
correct; actual RPM signing and verification happen when a package needs signing.

`config show` can include `key_fingerprint` even without `--all`. Active RPM package
settings can also include `key_snapshot_sha256`, `trusted_key_fingerprints`, and
`trusted_key_snapshot_sha256s`. Fingerprint and snapshot arrays are independently sorted;
do not pair them by index. These fields describe public identities and are output fields,
not accepted `sow.yml` keys.

See [Signing](/docs/feature/signing/) for rotation and package reuse.

## Publication targets

```yaml
targets:
  mirror:
    repository: demo
    provider: filesystem
    endpoint: file:///srv/mirror
    prefix: demo
    public_endpoint: file:///srv/mirror/demo/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

| Field | Required | Meaning |
|---|---|---|
| `repository` | Yes | Existing repository name |
| `provider` | Yes | `filesystem` or `r2` |
| `endpoint` | Yes | Canonical `file:///absolute/path` without a trailing slash, or `https://host` for R2 |
| `region` | R2 only | Must be `auto`; forbidden for filesystem |
| `bucket` | R2 only | Lowercase DNS-safe bucket label; forbidden for filesystem |
| `prefix` | No | Relative storage prefix; empty uses the storage namespace root |
| `credential` | R2 only | `env://NAME` or `file:///absolute/path`; forbidden for filesystem |
| `public_endpoint` | Yes | Canonical verification URL ending in `/`; filesystem accepts HTTP(S) or `file://`, R2 accepts HTTP(S) |
| `max_cache_ttl` | Yes | Canonical non-negative Go duration, including explicit `0s` |
| `authoritative_workspace` | Yes | Must be `true` |
| `single_writer` | Yes | Must be `true` |
| `exclusive_write_authority` | Yes | Must be `true` |
{.wide .expand}

The last three fields state that this workspace owns publication and is the only writer
for the target namespace. Targets on the same storage cannot have overlapping prefixes.
Filesystem targets cannot resolve to overlapping directories.

Use canonical durations such as `0s`, `30m0s`, or `24h0m0s`; `24h` is rejected.
Durations are bounded below Go's maximum duration to leave room for the cache-grace margin.
Set this value to cover the longest cache lifetime used by the public service.

Create the filesystem endpoint directory before publishing. It must be a real canonical
directory, not a symlink. SOW creates the prefix beneath it.

An R2 target adds storage and credential fields:

```yaml
targets:
  prod:
    repository: demo
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: demo
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/demo/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

The referenced environment variable or file contains one JSON document:

```json
{"access_key_id":"YOUR_ACCESS_KEY_ID","secret_access_key":"YOUR_SECRET_ACCESS_KEY"}
```

It can also contain `session_token`. Unknown fields, trailing data, missing credentials,
and values larger than 64 KiB are rejected. Credential files must resolve to regular files;
a symlink to a regular file is accepted. Credentials are not included in the public tree
or configuration output.

The first publication binds the repository, provider, storage identity, and prefix.
To change the target name, `public_endpoint`, or `max_cache_ttl`, use
[`publish --rebind`](/docs/command/publish/#rebind-mutable-target-settings).
Provider, endpoint, region, bucket, prefix, and repository identity cannot be rebound;
configure a new target. Pending maintenance can block changes to cache TTL or the public
endpoint until that maintenance completes.

<span id="what-is-not-in-sowyml" data-td-print-local></span>

## Fixed settings

Repository paths are always `<workspace>/<name>`. APT components are always `main`.
Architecture views are derived from Dist configuration and package headers. Generation
retention is managed with [`retain`](/docs/command/retain/), not a configuration count.

See [Layout](/docs/reference/layout/), [Publication](/docs/command/publish/), and
[Exit codes](/docs/reference/exit-codes/).

<span id="see-also" data-td-print-local></span>
