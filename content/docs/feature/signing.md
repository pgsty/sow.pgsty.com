---
title: "Signing Model"
linkTitle: "Signing Model"
description: "Configure metadata and RPM package signing, reference keys, and rotate signing identities."
categories: [Feature]
tags: [signing, rpm, apt]
url: "/docs/feature/signing/"
weight: 600
icon: fa-solid fa-key
---

Configure metadata signing to let clients verify repository indexes. Configure RPM package
signing separately when clients also need to verify signatures embedded in RPM files.

<span id="two-independent-trust-chains" data-td-print-local></span>
<span id="what-the-client-verifies" data-td-print-local></span>

## What gets signed

| Setting | Signed content | Output | Client setting |
|---|---|---|---|
| `signing.rpm.metadata` | RPM index manifest | `repodata/repomd.xml.asc` | DNF `repo_gpgcheck=1` |
| `signing.deb.metadata` | APT release manifest | `InRelease`, `Release.gpg` | APT `Signed-By` |
| `signing.rpm.packages` | RPM package | Embedded OpenPGP signature | DNF `gpgcheck=1` |
{.wide .expand}

Metadata signing leaves package bytes unchanged. RPM package signing changes package
bytes and therefore their SHA-256. SOW does not add signatures to DEB package files.

<span id="configuration" data-td-print-local></span>

## Configure metadata signing

```yaml
repos:
  demo:
    signing:
      rpm:
        metadata:
          key: file:///secure/repo-signing.asc
      deb:
        metadata:
          key: file:///secure/repo-signing.asc
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

RPM and DEB can use the same key or different keys. For a protected key, add
`passfile: /run/secrets/gpg-password` next to `key`, or set `SOW_GPG_PASSFILE` to the
password-file path. Validate the settings, then build:

```bash
sow config check
sow build -r demo
sow check -r demo
```

Signed empty Dists receive the same signature files as populated Dists. The signed body
of `InRelease` matches `Release`. Without a configured key, SOW produces unsigned indexes.
Managed keys and signing policy come from `sow.yml`. `--passfile PATH` overrides the
password source for one invocation, including `build`.

<span id="four-key-reference-forms" data-td-print-local></span>

## Key and passphrase references

| Metadata key reference | Meaning | Signing implementation |
|---|---|---|
| `keys/repo.asc` | OpenPGP key file relative to the workspace root | In-process |
| `file:///secure/repo.asc` | OpenPGP key file at an absolute path | In-process |
| `env://SOW_METADATA_KEY` | Armored key material, file path, or GPG key identifier | Depends on the value |
| `agent://KEY_ID_OR_FINGERPRINT` | Key available through the local GPG environment | External `gpg` |
{.wide .expand}

Key files support ASCII-armored and binary OpenPGP data. A GPG key identifier is a
16-digit key ID or a 40- or 64-digit fingerprint. References that resolve to a GPG key
identifier use external `gpg` for private-key access. An explicit password file enables
noninteractive unlocking through GPG loopback mode.

A signing `key` reference must resolve to exactly one primary key.
A `trusted_keys` file can contain several complete public keys, including consecutive armored blocks.
SOW reads the complete bundle and rejects malformed or truncated input. It does not silently use only the first key.

Use `--passfile PATH`, per-key `passfile`, or `SOW_GPG_PASSFILE`, in that priority order.
Legacy metadata `passphrase` references remain supported at the per-key priority;
`passfile` and `passphrase` cannot both be nonempty on one key. All three signing settings
accept `passfile`, including `agent://` keys.

Password files contain one nonempty UTF-8 line. SOW removes exactly one final LF or
CRLF and preserves spaces and tabs. It does not search a default path or fall back
from an invalid selected source. See [Password files](/docs/reference/config/#passfile)
for the full format, relative-path rules, permissions, and recovery command coverage.

`config show` displays references and resolved public identities, not private-key or
passphrase contents. `config check` unlocks metadata key files and checks their
suitability; external GPG metadata keys also perform a signing probe. RPM package
signing checks credential format, tools, and secret-key availability, without signing
a package or proving the password correct. See [`config check`](/docs/command/config/#sow-config-check).
For new metadata signatures, the selected signing key must be usable at the publication
time and at the current time. Historical verification uses the retained certificate.

New APT signatures use SHA-256. A new publication requires SHA-256, SHA-384, or SHA-512 in
both APT signature files. If upgrading a workspace with SHA-1 metadata signatures, run
`build` before starting a new publication. An existing publication attempt resumes its
recorded files.

<span id="rpm-package-signing" data-td-print-local></span>
<span id="trust-rings-are-verified-independently" data-td-print-local></span>

## Configure RPM package signing

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      trusted_keys: [keys/upstream.asc]
```

| Mode | Behavior |
|---|---|
| `never` | Store the input bytes unchanged |
| `fill` | Keep a package whose signature verifies with the configured key or trusted keys; sign other packages |
| `always` | Keep a package already signed by the configured key; re-sign other packages |
{.wide .expand}

With no key, the default mode is `never`. With a key, the default is `fill`.
Both `fill` and `always` require a key.

Package signing uses the host `rpm --addsign` or `rpm --resign` command on a private
copy. Install `rpm` and `gpg`, and make the matching private key available in the GPG
environment used by `rpm`. A key reference identifies the signer; it does not import a
private key into that environment. SOW leaves the original input file unchanged.

SOW checks the result's signature, package coordinate, and signature-neutral payload
digest. If an existing object has the same coordinate and payload and satisfies the
current policy, SOW can reuse its signed bytes. In `never` mode, reuse requires an exact
byte match.

Use RPM format v4 for package-signing workflows. SOW verifies RSA, DSA, ECDSA, and EdDSA RPM signatures, including header-only signatures stored in RPM signature header tag 267 (`RPMSIGTAG_DSA`). SOW does not support the signature tag
used by RPM format v6. This is separate from OpenPGP packet versions; SOW supports historical CentOS
OpenPGP v3 and v4 signatures.

<span id="key-changes-make-dists-dirty" data-td-print-local></span>

## Change keys

Changing only a `passfile` path does not make Dists dirty. A changed signing identity does. For metadata keys, run `build` to
create signatures with the new identity. Distribute the new public key to clients before
publishing the new metadata.

Existing pool objects are immutable. Changing RPM package policy does not re-sign them
in place. For a staged package-key rotation:

1. Set the new key as current and use `mode: fill`.
2. Keep the old public key in `trusted_keys` while old packages remain members.
3. Add new package releases signed by the new key.
4. Remove old trust after you withdraw or replace the old signed packages.
{.steps .td-steps-compact}

Switching directly to `always` with a new key requires every Desired RPM to satisfy that
key policy. If changed signatures would replace an existing package URL with different
bytes, publish a new package release and filename.

RPM verification evaluates certificate and signing-subkey validity at the package's
signature time. Renewing a certificate does not itself invalidate old signatures when
the required historical self-certifications and subkey bindings remain in the certificate.
Keep that historical public-key material when exporting renewed keys.

<span id="plain-mode" data-td-print-local></span>

## Plain signing

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73 --passfile /run/secrets/gpg-password
sow create /srv/offline --sign-with 6D5C5A26C36B1F73 --overwrite --passfile /run/secrets/gpg-password
```

Plain mode signs RPM package files only. Without `--overwrite`, it signs packages with
no parseable embedded signature. With `--overwrite`, it re-signs all retained RPMs.
The key is 16, 40, or 64 hexadecimal characters, with an optional `0x` prefix.
At least one RPM must remain after any `--pigsty` cleanup.

See [Sign your repository](/docs/tutorial/signing/) for client setup and
[Configuration](/docs/reference/config/) for all signing fields.

<span id="next" data-td-print-local></span>
