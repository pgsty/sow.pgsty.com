---
title: "Package References"
linkTitle: "Package References"
description: "The five ways to name a package on the command line, and how ambiguity is resolved."
url: "/docs/reference/package-ref/"
weight: 300
icon: fa-solid fa-fingerprint
---

`sow rm`, `sow show`, and `sow where` all take a `PACKAGE` argument. This page defines
what you may write there. The same grammar applies to all three commands; only the
handling of an ambiguous name differs.

Nothing here applies to `sow add`, which takes filesystem paths, not references.

## The five forms

| Form | Example | Matches |
|---|---|---|
| Content digest | `sha256:d06d7f23b9cf...b98b1229` | Exactly one package object |
| RPM coordinate | `rpm:pev2-0:1.23.0-1.noarch` | Exactly one RPM |
| DEB coordinate | `deb:libpq5=18.3-1.pgdg12+1:amd64` | Exactly one DEB |
| Filename | `pev2-1.23.0-1.noarch.rpm` | The package stored under that filename |
| Bare name | `pev2` | Every version and architecture of that name |

The first three are exact: they name one object and either hit it or fail. The last two
are conveniences that may match more than one object.

You never have to construct these by hand. `sow ls` prints the digest and the coordinate
of every package, in a form you can paste straight back into another command:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18	rpm:blackbox_exporter-0:0.28.0-1.x86_64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229	rpm:pev2-0:1.23.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

### Content digest

```text
sha256:<64 lowercase hex digits>
```

The SHA-256 of the complete stored package bytes. This is the strongest reference SOW
has: it is the object's identity, so it can never be ambiguous.

```bash
sow where sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229
```

```console
{"reference":"sha256:d06d7f23...b98b1229","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d06d7f23...b98b1229","coordinate":"rpm:pev2-0:1.23.0-1.noarch"}]}
```

The digest must be complete and lowercase. There is no prefix matching and no
case-folding — a short or uppercase digest is a usage rejection, not a failed lookup:

```console
operation rejected: managed: operation rejected: sha256 reference requires 64 lowercase hexadecimal digits
```

Note that this digest covers the bytes **as stored**. If a repository re-signs RPM
payloads, the digest of the object differs from the digest of the file you handed to
`sow add`.

### RPM coordinate

```text
rpm:<name>-<epoch>:<version>-<release>.<arch>
```

The full NEVRA, prefixed with `rpm:`. Every component is required, including the epoch —
`0` when the package has none.

```bash
sow where 'rpm:pev2-0:1.23.0-1.noarch'
```

Quote it in a shell: NEVRA contains a colon, and history expansion or path completion can
otherwise mangle it.

Both the prefix and the epoch are load-bearing. Dropping either turns the string into a
bare-name lookup that finds nothing:

```console
sow where 'rpm:pev2-1.23.0-1.noarch'
operation rejected: managed: operation rejected: package reference "rpm:pev2-1.23.0-1.noarch" was not found in the selected Workspace scope
```

The architecture component is the one from the RPM header: `x86_64`, `aarch64`, or
`noarch`. It is not the canonical family — a `noarch` package is written `noarch` here,
even though SOW classifies it internally as neutral.

### DEB coordinate

```text
deb:<package>=<version>:<architecture>
```

The Debian identity triple, prefixed with `deb:`. The version is the complete Debian
version including epoch and revision; the architecture is the ecosystem name (`amd64`,
`arm64`, `all`), not the canonical family.

```bash
sow where 'deb:libpq5=18.3-1.pgdg12+1:amd64'
```

All three parts are required. `deb:libpq5=18.3-1.pgdg12+1` without an architecture does
not match anything.

### Filename

The complete filename of the package as stored, including the extension:

```bash
sow where 'pev2-1.23.0-1.noarch.rpm'
sow where 'libpq5_18.3-1.pgdg12+1_amd64.deb'
```

This is the easiest form to type when you are looking at a directory listing. It is not
an identity, though: filename is not what SOW uses to tell packages apart, and two
distinct objects could in principle carry the same name. Prefer a coordinate or a digest
in scripts.

### Bare name

Just the binary package name:

```bash
sow where pev2
```

What this means depends on the command:

- **`sow rm`** treats it as *every* version and native architecture of that name in the
  selected distributions. This is intentional — removing a package usually means removing
  all of it. Preview first with `-c`:

  ```bash
  sow rm libpq5 -d trixie -c
  ```

  ```console
  {"repository":"pigsty","desired_revision":10,"built_generation":"00000000000000000010","dirty":false,"check":true,
   "removed":[{"dist":"trixie","sha256":"310611d0...","coordinate":"deb:libpq5=18.2-1.pgdg12+1:amd64","name":"libpq5"},
              {"dist":"trixie","sha256":"4b526223...","coordinate":"deb:libpq5=18.3-1.pgdg12+1:amd64","name":"libpq5"},
              {"dist":"trixie","sha256":"cadeb929...","coordinate":"deb:libpq5=18.3-1.pgdg12+1:arm64","name":"libpq5"}], ...}
  ```

- **`sow show` and `sow where`** require it to identify exactly one object. They describe a
  single package, so a name matching several is refused with the candidate list:

  ```console
  operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1.pgdg12+1:amd64 sha256:310611d0fea1ce82644f48d90d485c60738b21e52ab5a60e1de43875bdfef601, deb:libpq5=18.3-1.pgdg12+1:amd64 sha256:4b5262231787caf1f367f5c8705a8a03d3176c31a15e6096946d50514db128be, deb:libpq5=18.3-1.pgdg12+1:arm64 sha256:cadeb9294901ac5ae6228bd3471c444cc288d9894af0dd0730909596d9dfcefb
  ```

  Every candidate is printed with both its coordinate and its digest, so the fix is to
  copy one of them back onto the command line.

## What does not work

A NEVRA without the `rpm:` prefix looks like a coordinate but is parsed as a bare name,
and bare names do not contain epochs or architectures:

```console
sow rm 'pev2-0:1.23.0-1.noarch' -d el9 -c
operation rejected: managed: operation rejected: package reference not found: package reference "pev2-0:1.23.0-1.noarch" matches no Desired Membership
```

There is also no glob, no regex, no version range, and no `--all` flag. If you want to
select a set of packages by pattern, that is [membership policy](/docs/reference/config/)
in `sow.yml`, not a command-line selector. The command line only ever names packages that
already exist.

## Scope

A reference is resolved within a scope, and the scope is set by the usual selection flags,
not by the reference:

| Command | Default scope | Narrow with |
|---|---|---|
| `sow rm` | The selected distributions of the selected repository | `-r`, `-d` (required when several exist) |
| `sow show` | The selected repository | `-r`, `-d` |
| `sow where` | Every repository in the workspace | `-r`, `-d` |

`sow where` is the one that searches broadly — use it when you know a package exists
somewhere but not where. `sow show` describes one object in one repository in full detail.

The two commands also word their misses differently, which tells you which one you ran:

```console
# rm — the reference resolved, but nothing in the selected dists matches it
operation rejected: ... package reference "nosuchpkg" matches no Desired Membership

# show / where — nothing in the searched scope matches at all
operation rejected: ... package reference "nosuchpkg" was not found in the selected Workspace scope
```

## Coordinates and identity

The coordinate forms above are the *logical* identity of a package, and SOW enforces that
one coordinate maps to at most one content object inside a repository. Adding a different
file under a coordinate that already exists is a hard conflict — SOW will not silently
pick a winner, and there is no `--replace`.

Two packages that differ only in signature therefore still collide, because the coordinate
is the same. If you re-sign a package for real, bump its release; if you are re-adding the
identical input, SOW recognizes it and reports `reused`.

## See also

- [`sow rm`](/docs/command/rm/) — removal, preview, and batch semantics
- [`sow ls`](/docs/command/ls/), [`show`](/docs/command/show/), and [`where`](/docs/command/where/) — the query commands
- [Exit Codes](/docs/reference/exit-codes/) — `6` covers both "no match" and "ambiguous"
