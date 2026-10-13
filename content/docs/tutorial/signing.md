---
title: "Sign Your Repository"
linkTitle: "Sign Your Repository"
description: "Sign RPM and APT metadata, optionally sign RPM packages, and enable client verification."
categories: [Tutorial]
tags: [signing, apt, yum]
url: "/docs/tutorial/signing/"
weight: 300
icon: fa-solid fa-key
---

Repository signing has two layers: metadata signatures and RPM package signatures. Configure each layer separately:

| Path | Output | Client control |
|---|---|---|
| RPM metadata | `repodata/repomd.xml.asc` | `repo_gpgcheck=1` |
| APT metadata | `InRelease` and `Release.gpg` | `Signed-By` |
| RPM package body | embedded RPM signature | `gpgcheck=1` |

APT verifies package hashes through the signed `Release` file, so DEBs need no separate package signature. Start with metadata signing. Add RPM package signing when clients require `gpgcheck=1`.

This guide uses the `pigsty` Repository from the [YUM](/docs/tutorial/yum-repo/) or [APT](/docs/tutorial/apt-repo/) tutorial. Run only the commands for the formats and Dists you created.

## 1. Create a dedicated key

Install GPG first. These commands create an unencrypted test key and export it to a private directory. For an existing protected key, use a `passphrase` reference as described below.

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

SOW reads the private key from `/srv/sow-secrets`, outside the public Repository. Give the SOW service account access to this directory if it differs from your user. Distribute `repo-signing.pub` to clients.

## 2. Configure metadata signing

In `/srv/sow/sow.yml`, merge these metadata entries into the Repository's existing `signing` block. Keep its package policy and Dist definitions. Include only the formats you use:

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

Validate the configuration, rebuild, and check:

```bash
cd /srv/sow
sow config check
sow build -r pigsty
sow check -r pigsty
```

For a protected key, add `passphrase: env://SOW_METADATA_PASSPHRASE` next to `key`, then supply that environment variable to SOW. You can also use a passphrase file or `agent://FINGERPRINT` to sign through GPG. See [passphrase references](/docs/reference/config/#passphrase-references). Configuration stores references, not secret values.

## 3. Optional: inspect the metadata signer {#3-verify-metadata-manually}

The preceding `sow check` verifies metadata signatures. To inspect the signer with GPG,
run the commands for your Dists:

```bash
gpg --verify \
  pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
  pigsty/dists/el9/x86_64/repodata/repomd.xml

gpg --verify pigsty/dists/trixie/InRelease
gpg --verify \
  pigsty/dists/trixie/Release.gpg \
  pigsty/dists/trixie/Release
```

Compare the displayed fingerprint with the public key you distribute to clients.

## 4. Optional: sign RPM package bodies

For a new repository, configure package signing before importing RPMs. Add this block under the existing `signing.rpm` configuration:

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

Replace the placeholder with the 40-hex fingerprint in `$FPR`. Install `rpm` and `gpg`,
and make the secret key available in the GPG keyring used by `rpm`.

`fill` signs newly imported packages unless their signatures already verify against the
configured key or `trusted_keys`. See [RPM signing policy](/docs/reference/config/) for
other modes.

SOW signs a private copy during `add`; the input file stays unchanged. `build` checks stored RPMs against the policy but does not re-sign them.

If you already imported RPMs, check their signatures before enabling `fill`. Keep trusted upstream public keys in `trusted_keys`. For unsigned or untrusted stored packages, prepare correctly signed packages with new versions and filenames. Alternatively, configure signing in a new repository, then import the originals.

After configuring the policy, import a new package and check the result:

```bash
sow config check
sow add /path/to/new.rpm -r pigsty -d el9
sow check -r pigsty
```

To inspect a resulting package independently, run `rpmkeys --checksig` on its file in
`pigsty/pool/`.

## 5. Enable dnf verification

First [publish the signed Repository](/docs/tutorial/serving/). Then transfer the public
key to the client through a trusted channel:

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

If you sign only metadata, use `repo_gpgcheck=1` and `gpgcheck=0`. With package checking enabled, install each trusted upstream package key as well as your own key. Then run `sudo dnf makecache --refresh` and install a package.

## 6. Enable APT verification

After [publishing the signed Repository](/docs/tutorial/serving/), install its public key
on the client as a dedicated keyring:

```bash
sudo gpg --dearmor --yes \
  --output /usr/share/keyrings/pigsty-archive-keyring.gpg /path/to/repo-signing.pub
sudo chmod 0644 /usr/share/keyrings/pigsty-archive-keyring.gpg
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

Run `sudo apt update` and install a package. If verification fails, compare the client keyring fingerprint with the signer shown by `gpg --verify`. For ARM64 clients, change `Architectures` to `arm64`.

## Plain-mode RPM signing

Plain mode can sign RPM package bodies, but it does not sign repository metadata or create
an APT `Release`:

```bash
sow create /srv/flat --sign-with 0123456789ABCDEF
```

Replace `0123456789ABCDEF` with your key ID or fingerprint. The matching private key must
be available to `rpm` and GPG. Existing signatures, including upstream signatures, are
preserved. To replace all RPM signatures with your key, use `--overwrite` on a separate
working copy. See [`sow create`](/docs/command/create/#signing-rpms) for key formats.

For an existing YUM repository, follow the [migration guide](/docs/tutorial/yum-migration/)
to preserve publication time and sign `repomd.xml` after the final `create` run.

## Key changes

To rotate a metadata key, distribute the new public key, update the key reference, then run `build`, `check`, and `publish`. Changing the reference or resolved fingerprint marks affected Dists dirty.

For RPM package keys, use `fill` and keep the old public key in `trusted_keys` until packages signed by it are withdrawn or replaced. Keep the corresponding client key available during this period. Existing package objects remain unchanged.

Test the final repository with the DNF or APT versions your users run. See [Platforms & Integrations](/docs/reference/compatibility/) for automated coverage.
