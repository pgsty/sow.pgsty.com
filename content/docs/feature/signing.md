---
title: "Signing Model"
linkTitle: "Signing Model"
description: "Two independent trust chains, four key-reference forms, in-process versus external signing, and safe key changes."
url: "/docs/feature/signing/"
weight: 600
icon: fa-solid fa-key
---

There are two different questions a client can ask about a repository, and SOW answers them with two separate mechanisms. Confusing them is the most common source of "I signed it but `dnf` still complains", so this page starts by pulling them apart.

## Two independent trust chains

| | Metadata signing | RPM package signing |
|---|---|---|
| Question answered | "Is this index really from you, and unmodified?" | "Is this `.rpm` file really from you?" |
| Configured by | `signing.rpm.metadata`, `signing.deb.metadata` | `signing.rpm.packages` |
| Produces | `repodata/repomd.xml.asc`, `InRelease`, `Release.gpg` | an OpenPGP signature embedded in the package |
| Changes package bytes | no | yes |
| Client setting | dnf `repo_gpgcheck=1`, apt `Signed-By` | dnf `gpgcheck=1` |
| Available in Plain mode | no | yes, via `create -S KEY` |

They are configured separately and can be used separately. Metadata signing alone is usually the right starting point: it authenticates the whole index in one place and requires no change to the packages you received from upstream.

Managed metadata signing is controlled entirely by `sow.yml`. There is no CLI override, no `--sign` flag on `build`, and no way to sign one build differently from the next. That is deliberate — a repository's signing identity is a property of the repository, not of the command that happened to update it.

## Configuration

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never              # never | fill | always
        metadata:
          key: "file:///secure/repo-signing.asc"
      deb:
        metadata:
          key: "file:///secure/repo-signing.asc"
```

RPM and DEB metadata keys are declared separately, so you can use the same key for both (as above) or split them. Each metadata block accepts an optional `passphrase` reference alongside `key`.

With a metadata key configured, every build produces the signature files, including for an empty Dist:

- RPM, per architecture view: `repodata/repomd.xml` plus an ASCII-armored `repodata/repomd.xml.asc`
- DEB, per Dist: `Release` plus a clearsigned `InRelease` and a detached armored `Release.gpg`

The clearsigned body of `InRelease` is identical to `Release`. Without a metadata key, neither signature file is generated at all — you get `repomd.xml` and `Release` and nothing else.

## Four key-reference forms

A key reference is a URI, and the scheme decides who does the signing:

| Reference | Meaning | Signer |
|---|---|---|
| `keys/repo-signing.asc` | an ASCII-armored key at a path relative to the Workspace root | in-process Go signer |
| `file:///absolute/path.asc` | an ASCII-armored private key on disk | in-process Go signer |
| `env://VAR_NAME` | the armored key material in an environment variable | in-process Go signer |
| `agent://<fingerprint>` | a key held by the GPG agent in your environment | external `gpg` |

`file://` and `env://` need nothing installed — SOW signs metadata itself, which is why a repository with `file://` metadata keys builds identically on macOS and inside a minimal container. `agent://` delegates to your GPG agent, which is the right choice when the private key lives on a smartcard or must never touch a file. `agent://` cannot be combined with a `passphrase` reference, because the agent owns that interaction.

A `passphrase` reference accepts a Workspace-relative path, `file://`, or `env://`; it
does not accept `agent://`.

**Nothing secret is ever persisted.** Configuration, SQLite, logs, JSON output, and error text hold only the reference string, the fingerprint, and the public verifier certificate. `config show --all` prints references and fingerprints, never key material. If a key reference is unresolvable or unusable for signing, `config check` says so before you run a build.

## RPM package signing

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      trusted_keys: [keys/pgdg.asc]
```

Three modes:

| Mode | Behavior |
|---|---|
| `never` | keep the input bytes exactly as given |
| `fill` | sign when the package is unsigned or its signature is not trusted; keep the bytes when an existing signature verifies against `trusted_keys` |
| `always` | ensure the final package is validly signed by the configured key; keep the bytes if it already is, otherwise re-sign |

`trusted_keys` automatically includes the public half of the configured `key`. Without a key, `never` is the only legal mode. `fill` is the default when a key is present.

Package signing always runs `rpm --addsign` or `rpm --resign` from your environment, on a
private staged copy. Your input file is never modified in place. After signing, SOW
re-parses the result and requires an embedded signature, unchanged signature-neutral
digest and NEVRA, and the exact configured public-key identity. The `rpm` and `gpg`
executables and a matching secret key in the GPG environment used by `rpm` are mandatory
for `fill` and `always`. A key reference identifies and verifies the signer; it does not
provision the secret key into that environment.

Because signatures embed a timestamp, signing is not reproducible — the same unsigned RPM signed twice gives different bytes. Re-adding a package you already added would therefore look like a content conflict. SOW avoids that with a **signature-neutral payload digest**: a SHA-256 over the immutable header and payload, excluding the RPM signature header. If the logical coordinate already exists and the neutral digest matches, and the existing object satisfies the current policy, SOW reuses the existing final bytes instead of signing again. Repeated `add` of the same package is a stable no-op.

That reuse is narrow on purpose. `never` requires a full byte match, since that mode promises to preserve input bytes. If the payload digest differs, or the stored object does not satisfy the current signing policy, it is a hard conflict — `add` will not quietly re-sign a package in place under an existing coordinate. There is no `--replace`; if re-signing changes the bytes, bump the release, or plan a proper key-rotation workflow.

## Key changes make Dists dirty

A Dist's Built configuration digest covers its format, canonical architectures, `limit`, `exclude`, and the **frozen signing identity**. Change a key reference or a fingerprint and the digest changes, so every affected Dist becomes dirty:

```console
$ sow status
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9,trixie pending=0/0 locked=false
```

For a **metadata** key change, `sow build` signs the indexes with the new identity and
produces a new Generation.

RPM package bodies are immutable Package Objects. `build` does not silently re-sign an
existing object under the same coordinate. If current Desired RPMs do not satisfy the new
package-signing policy, `build` rejects the change. A staged rollover normally uses
`fill`, makes the new key current, and keeps the old public key in `trusted_keys`; existing
old-key packages retain their bytes while newly ingested packages use the new key. Remove
the old trust only after those package coordinates have been withdrawn or replaced by new
releases. Switching directly to `always` with a new key is valid only when every Desired
RPM is already signed by that key.

The exact public certificate identity of the current built metadata is recorded per Dist, and multiple certificate versions for the same primary fingerprint can coexist — so extending an expiry or adding a subkey does not invalidate what is already published.

## Plain mode

```bash
sow create /srv/repo --sign-with 6D5C5A26C36B1F73
sow create /srv/repo --sign-with 6D5C5A26C36B1F73 --overwrite
```

Plain mode signs RPM package bodies only; it has no metadata signing. `KEY` is exactly 16, 40, or 64 hexadecimal characters, without an `0x` prefix; it is normalized to uppercase and passed to `rpm` as the `_gpg_name` macro. Without `--overwrite`, only RPMs with no parseable embedded signature are signed. With it, every retained RPM is re-signed.

`--sign-with` requires at least one top-level RPM retained after `--pigsty` cleanup. A DEB-only directory, a missing `rpm` binary, or an unavailable key fails before anything public changes. Signing is an explicit slow path with necessary copy, signature-verification, and final-RPM parse reads; if interrupted, rerun from the current package directory rather than replaying a Plain journal. See [Plain Flat Repositories](/docs/feature/plain/).

## What the client verifies

```ini
[pigsty-el9]
name=Pigsty EL9
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch/
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://repo.example.com/keys/repo-signing.asc
```

```text
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Signed-By: /etc/apt/keyrings/repo-signing.asc
```

`repo_gpgcheck=1` makes dnf verify `repomd.xml.asc`; `gpgcheck=1` makes it verify each
package's embedded signature. On the APT side, `Signed-By` makes apt verify `InRelease`.
Automated checks validate generated signatures directly. Complete signed Managed dnf/APT
acceptance must run with real clients in the target environment; see
[Platforms & Integrations](/docs/reference/compatibility/) for the exact evidence.

`sow check` verifies every declared signature and file hash as part of its normal run, so a signing misconfiguration shows up before you ship rather than on a customer's machine.

## Next

- [Sign Your Repository](/docs/tutorial/signing/) — generating a dedicated key and wiring up both chains
- [`sow.yml` reference](/docs/reference/config/) — the full signing schema and key reference grammar
- [Observability & Audit](/docs/feature/audit/) — how `check` proves the signatures
