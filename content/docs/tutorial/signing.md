---
title: "Sign Your Repository"
linkTitle: "Sign Your Repository"
description: "Sign RPM and APT metadata, optionally sign RPM packages, and enable client verification."
url: "/docs/tutorial/signing/"
weight: 300
icon: fa-solid fa-key
---

SOW has two independent signing paths:

| Path | Output | Client control |
|---|---|---|
| RPM metadata | `repodata/repomd.xml.asc` | `repo_gpgcheck=1` |
| APT metadata | `InRelease` and `Release.gpg` | `Signed-By` |
| RPM package body | embedded RPM signature | `gpgcheck=1` |

APT trusts package hashes through the signed `Release`; SOW does not re-sign DEB package
bodies. Start with metadata signing. Add RPM package signing only when you own the signing
policy for those package bytes.

## 1. Create a dedicated key

The commands below create an unencrypted example key. Use a protected key and a
`passphrase` reference for production; see the [configuration reference](/docs/reference/config/#passphrase-references).

```bash
SIGNING_UID='SOW Repository <repo@example.com>'
gpg --batch --pinentry-mode loopback --passphrase '' \
  --quick-generate-key "$SIGNING_UID" rsa3072 sign 2y

FPR="$(gpg --batch --with-colons --list-secret-keys "$SIGNING_UID" \
  | awk -F: '$1 == "fpr" {print $10; exit}')"
test -n "$FPR"

sudo install -d -m 0700 /srv/sow-secrets
sudo chown "$(id -u):$(id -g)" /srv/sow-secrets
gpg --batch --pinentry-mode loopback --passphrase '' --armor \
  --export-secret-keys "$FPR" > /srv/sow-secrets/repo-signing.asc
gpg --armor --export "$FPR" > /srv/sow-secrets/repo-signing.pub
chmod 600 /srv/sow-secrets/repo-signing.asc
```

Keep the secret key outside the Workspace's public Repository tree and outside every web
root. If a dedicated service account runs SOW, make that account—not the interactive
user—the directory owner. Distribute only `repo-signing.pub` to clients.

## 2. Configure metadata signing

In `/srv/sow/sow.yml`, add the relevant blocks under the Repository. Omit the ecosystem
you do not use:

```yaml
repos:
  pigsty:
    signing:
      rpm:
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
      deb:
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
    dists:
      # existing Dist definitions remain here
```

Validate the key reference, rebuild, and run the publication gate:

```bash
cd /srv/sow
sow config check
sow build -r pigsty
sow check -r pigsty
```

For a protected key, add `passphrase: env://SOW_METADATA_PASSPHRASE` or a bounded file
reference next to `key`. SOW never writes key or passphrase material into configuration,
SQLite, JSON, or logs.

## 3. Verify metadata manually

Use the exact paths for your Dists and architectures:

```bash
gpg --verify \
  pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
  pigsty/dists/el9/x86_64/repodata/repomd.xml

gpg --verify pigsty/dists/trixie/InRelease
gpg --verify \
  pigsty/dists/trixie/Release.gpg \
  pigsty/dists/trixie/Release
```

`sow check` verifies the configured signing identity as part of its deeper consistency
checks. Manual verification is still useful when establishing a client trust root.

## 4. Optional: sign RPM package bodies

Add `rpm.packages` only if clients require embedded package signatures:

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: fill
          key: agent://REPLACE_WITH_THE_FINGERPRINT
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
```

Replace the placeholder with the 40-hex fingerprint printed in `$FPR`. For this operation:

- `rpm` and `gpg` must be installed;
- the matching secret key must be available in the ambient GPG environment used by `rpm`;
- `fill` preserves packages already signed by the configured or `trusted_keys` identities;
- `always` re-signs everything not already signed by the configured identity;
- `never` leaves input bytes unchanged.

SOW invokes `rpm --addsign` or `rpm --resign` on a private staged copy, not on the input
file. Revalidate and rebuild after changing the policy:

```bash
sow config check
sow build -r pigsty
sow check -r pigsty
```

Inspect a resulting package with `rpmkeys --checksig /path/to/package.rpm`.

## 5. Enable dnf verification

Transfer the public key to the client through a trusted channel:

```bash
sudo install -m 0644 /path/to/repo-signing.pub /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
```

Then enable the checks that correspond to what you signed:

```ini
[pigsty-el9]
name=Pigsty EL9
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch/
enabled=1
repo_gpgcheck=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
```

Set `gpgcheck=0` if package-body signing is not configured. Do not disable
`repo_gpgcheck` after configuring metadata signing.

## 6. Enable APT verification

Install the public key as a dedicated keyring:

```bash
sudo gpg --dearmor --yes \
  --output /usr/share/keyrings/pigsty-archive-keyring.gpg /path/to/repo-signing.pub
```

Reference it from deb822 configuration and do not set `Trusted: yes`:

```ini
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/pigsty-archive-keyring.gpg
```

Run `apt update` and treat any signature error as a failed deployment, not as a reason to
weaken the client configuration.

## Plain-mode RPM signing

Plain mode can sign RPM package bodies, but it does not sign repository metadata or create
an APT `Release`:

```bash
sow create /srv/flat --sign-with 0123456789ABCDEF
```

The key must be exactly 16, 40, or 64 hexadecimal characters, with no `0x` prefix, and the
matching private key must be usable by the ambient `rpm`/GPG setup. Without `--overwrite`,
already signed RPMs keep their bytes; adding `--overwrite` explicitly re-signs every RPM.
SOW signs private staged copies before replacing package bytes and metadata.

## Key changes

Changing a key reference or resolved fingerprint marks affected Dists dirty. A metadata
key can be changed by distributing the new public key, rebuilding, checking, and then
switching client enforcement. RPM package keys need a staged rollover: Package Objects
are immutable, and `build` rejects stored RPMs that do not satisfy the new policy instead
of re-signing them in place. Use `fill` with the old public key in `trusted_keys` until old
package coordinates have been withdrawn or replaced. Finish with a real client acceptance
test in the target environment.

Run the final signed repository through the exact dnf/APT versions and trust policy used
in production. The automated scope is listed under
[Platforms & Integrations](/docs/reference/compatibility/).
