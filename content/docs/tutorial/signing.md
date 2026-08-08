---
title: "Sign Your Repository"
linkTitle: "Sign Your Repository"
description: "Generate a dedicated GPG key, sign repository metadata and RPM packages, and configure clients to reject anything unsigned."
url: "/docs/tutorial/signing/"
weight: 300
icon: fa-solid fa-key
---

An unsigned repository is a repository anyone on the path can rewrite. This tutorial closes that
hole: you generate a signing key, configure SOW to sign what it publishes, verify the signatures
by hand, and turn on client-side enforcement so `dnf` and `apt` refuse anything that does not
check out.

Plan for about twenty minutes.

## Two independent trust chains

Package repositories have two things worth signing, and they are not the same thing.

**Repository metadata** answers "is this index the one the publisher produced?" For RPM that is a
detached signature over `repomd.xml`, published as `repodata/repomd.xml.asc`. For APT it is
`InRelease` (the `Release` content with an inline signature) and `Release.gpg` (a detached
signature over the same `Release`). SOW signs metadata in-process using a Go OpenPGP
implementation — no external `gpg` binary needed unless you point it at a GPG agent.

**Package payloads** answer "was this `.rpm` built by whom it claims?" That is a signature
embedded in the RPM header itself. It travels with the file, so it survives mirroring and
offline copies. SOW signs RPM packages by invoking `rpm --addsign` / `rpm --resign` on a private
staged copy, which means the `rpm` executable must be present.

DEB packages have no equivalent in-band signature in common practice; APT's trust comes from the
signed `Release`, which covers the index, which covers each package's SHA-256.

| | Signs what | Produces | Needs external tools |
|---|---|---|---|
| RPM metadata | `repomd.xml` | `repodata/repomd.xml.asc` | no (unless `agent://`) |
| APT metadata | `Release` | `InRelease`, `Release.gpg` | no (unless `agent://`) |
| RPM packages | the `.rpm` header | rewritten package bytes | yes — `rpm` and its GPG environment |

Configure them independently. Metadata signing is the one you want first: it is cheap, needs no
extra tooling, and is what `repo_gpgcheck` and `Signed-By` verify.

## Step 1: Generate a dedicated signing key

Do not reuse a personal key. A repository key gets copied to build hosts and lives for years;
give it its own identity so you can revoke it without collateral damage.

Write a batch parameter file:

```bash
mkdir -p ~/secure && chmod 700 ~/secure
cat > ~/secure/keyparams <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 4096
Key-Usage: sign
Name-Real: Pigsty Repository Signing Key
Name-Email: repo@example.com
Expire-Date: 0
%commit
EOF
gpg --batch --gen-key ~/secure/keyparams
```

```console
gpg: keybox '/home/you/.gnupg/pubring.kbx' created
gpg: /home/you/.gnupg/trustdb.gpg: trustdb created
gpg: directory '/home/you/.gnupg/openpgp-revocs.d' created
gpg: revocation certificate stored as '/home/you/.gnupg/openpgp-revocs.d/C811FBFBFE4031E5E2D7047904DD7F129A7B65E7.rev'
```

`Key-Usage: sign` gives a signing-only key with no encryption subkey — there is nothing to
encrypt here. `Expire-Date: 0` means no expiry; if you prefer a rotation cadence, set something
like `2y` and plan for [Step 8](#step-8-rotate-the-key).

`%no-protection` creates the key without a passphrase, which is what you want for unattended
builds where the file's permissions are the protection. To use a passphrase instead, replace
that line with `Passphrase: YOUR_PASSPHRASE` and see
[Step 6](#step-6-key-references-and-passphrases).

Find the fingerprint:

```bash
gpg --list-keys --keyid-format=long repo@example.com
```

```console
pub   rsa4096/04DD7F129A7B65E7 2026-08-04 [SC]
      C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
uid                 [ultimate] Pigsty Repository Signing Key <repo@example.com>
```

{{% alert title="Save the revocation certificate" color="warning" %}}
`gpg --gen-key` wrote a revocation certificate to `~/.gnupg/openpgp-revocs.d/`. Copy it
somewhere you can reach even if this host is gone. Without it you cannot tell clients the key is
dead.
{{% /alert %}}

## Step 2: Export both halves of the key

SOW reads an ASCII-armored **private** key to sign with. Clients need the armored **public** key
to verify.

```bash
FPR=C811FBFBFE4031E5E2D7047904DD7F129A7B65E7

gpg --armor --export-secret-keys "$FPR" > ~/secure/repo-signing.asc
chmod 600 ~/secure/repo-signing.asc

gpg --armor --export "$FPR" > ~/secure/RPM-GPG-KEY-pigsty
```

```bash
ls -l ~/secure
```

```console
-rw-------  1 you you  3457 Aug  4 12:25 repo-signing.asc
-rw-r--r--  1 you you  1709 Aug  4 12:25 RPM-GPG-KEY-pigsty
```

`repo-signing.asc` is a secret. `RPM-GPG-KEY-pigsty` is meant to be published — put it next to
the repository so clients can fetch it. The same file works for both ecosystems; the `RPM-GPG-KEY-`
prefix is only an Enterprise Linux naming convention.

## Step 3: Configure metadata signing

Signing is configured in `sow.yml` per repository. There is no command-line override — what
signed a tree is a property of the configuration, and it is recorded in the audit log.

```yaml
schema: sow/v3
architectures:
  - x86_64
  - aarch64

repos:
  pigsty:
    signing:
      rpm:
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
      deb:
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
      trixie:
        format: deb
```

`file://` takes an absolute path, so the reference has three slashes: `file://` plus `/home/...`.

Validate that the key resolves and is usable for signing before you build anything:

```bash
sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=2
```

`sow config show --all` expands defaults and reports the fingerprint SOW resolved — never the
key material:

```bash
sow config show --all
```

```console
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
        metadata:
          key: file:///home/you/secure/repo-signing.asc
          key_fingerprint: C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
      deb:
        metadata:
          key: file:///home/you/secure/repo-signing.asc
          key_fingerprint: C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 1
        exclude:
          - kind:
              - debuginfo
              - debugsource
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

Secret material never reaches configuration output, SQLite, the operation log, JSON, or error
text. If you see key bytes anywhere in SOW's output, that is a bug worth reporting.

## Step 4: Build the signed tree

The signing identity is part of what defines a built generation, so changing it makes every
affected Dist dirty:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=6 dirty_dists=el9,trixie pending=0/0 locked=false
```

```bash
sow build
```

```console
{"operation":"5414596509861246745","repository":"pigsty","dists":["el9","trixie"],"desired_revision":6,"built_generation":7,"noop":false,"dirty":false}
```

```bash
find pigsty/dists \( -name "*.asc" -o -name "InRelease" -o -name "Release.gpg" \) | sort
```

```console
pigsty/dists/el9/aarch64/repodata/repomd.xml.asc
pigsty/dists/el9/x86_64/repodata/repomd.xml.asc
pigsty/dists/trixie/InRelease
pigsty/dists/trixie/Release.gpg
```

One `.asc` per RPM architecture view, and both APT signature forms for the DEB Dist. `Release`
is still there unsigned alongside `InRelease` — some tooling still reads it, and `Release.gpg`
covers it.

## Step 5: Verify the signatures yourself

Do not take the build's word for it. Check all three:

```bash
gpg --verify pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
             pigsty/dists/el9/x86_64/repodata/repomd.xml
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

```bash
gpg --verify pigsty/dists/trixie/InRelease
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

```bash
gpg --verify pigsty/dists/trixie/Release.gpg pigsty/dists/trixie/Release
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

`InRelease` is a clearsigned document — the `Release` content is inside it verbatim:

```bash
head -13 pigsty/dists/trixie/InRelease
```

```console
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:25:13 UTC
X-SOW-Generation: 7
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
```

`sow check` verifies every declared signature as part of its full pass, so you get this for free
in CI:

```bash
sow check
```

```console
repository=pigsty status=clean ready_to_copy=true revision=6 generation=7
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=99
package-bytes	ok=true	checked=18
desired-membership	ok=true	checked=15
index	ok=true	checked=2
signature	ok=true	checked=20
generation-manifest	ok=true	checked=7
```

## Step 6: Key references and passphrases

`key:` accepts three reference forms.

`file:///absolute/path` reads an armored private key from disk and signs in-process. This is the
default choice: no external tooling, no agent, works identically on Linux and macOS.

`env://VARIABLE_NAME` reads the armored private key from an environment variable. Use this when
a secret manager injects credentials at run time and you would rather not write them to disk.
The variable holds the key itself, not a path:

```yaml
key: "env://SOW_METADATA_KEY"
```

```bash
sow config check
```

```console
operation rejected: managed: operation rejected: repository "pigsty" signing: rpm metadata key: environment key reference SOW_METADATA_KEY is unset
```

Exit code `6`. With the variable set:

```bash
SOW_METADATA_KEY="$(cat ~/secure/repo-signing.asc)" sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=2
```

`agent://FINGERPRINT` delegates to a running `gpg-agent`, so the private key never leaves the
agent — the right choice when it lives on a smartcard or YubiKey. This form calls the
environment's `gpg`, and it cannot take a passphrase reference: unlocking is the agent's job,
through pinentry or a preset.

### Passphrase-protected keys

For `file://` and `env://` keys that are protected, add a `passphrase:` alongside `key:`. It uses
the same reference grammar, so the secret can stay out of the file:

```yaml
signing:
  rpm:
    metadata:
      key: "file:///home/you/secure/repo-signing-2027.asc"
      passphrase: "env://SOW_METADATA_PASSPHRASE"
  deb:
    metadata:
      key: "file:///home/you/secure/repo-signing-2027.asc"
      passphrase: "env://SOW_METADATA_PASSPHRASE"
```

Missing it fails closed rather than producing an unsigned tree:

```bash
sow config check
```

```console
operation rejected: managed: operation rejected: repository "pigsty" signing: managed: resolve RPM metadata passphrase: environment passphrase reference is unset
```

```bash
SOW_METADATA_PASSPHRASE='...' sow build
```

## Step 7: Sign RPM packages

Metadata signing proves the index is yours. Package signing proves each `.rpm` is yours, which
keeps holding after someone mirrors your repository or copies a file out of it. This is what
`gpgcheck=1` on the client verifies.

Configure it under `signing.rpm.packages`:

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: fill
          key: "agent://C811FBFBFE4031E5E2D7047904DD7F129A7B65E7"
          trusted_keys: [keys/pgdg.asc]
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
```

There are three modes:

| Mode | Behaviour |
|---|---|
| `never` | keep input bytes exactly as given; the only mode allowed without a key, and the default |
| `fill` | sign packages that are unsigned or signed by an untrusted key; keep signatures that verify against `trusted_keys` |
| `always` | ensure every package is validly signed by the configured key; keep bytes when it already is, re-sign otherwise |

`fill` is the usual choice for a repository that mixes upstream packages with your own: upstream
signatures listed in `trusted_keys` survive, everything else gets yours. The configured key's own
public half is always included in `trusted_keys`, so you never have to list it.

Two constraints matter in practice. Package signing rewrites bytes, so the signed package — not
the input file — becomes the repository's object. And it requires the `rpm` executable to be
installed plus a GPG environment that can actually use the private key; without those, the
command fails before anything is published rather than quietly falling back to unsigned.

Your input files are never modified. Signing happens on a private staged copy, and the result is
re-parsed and verified — signature present, NEVRA unchanged, final SHA-256 recorded — before it
is allowed into the pool.

Re-adding the same unsigned RPM twice is still a no-op even though signatures embed a timestamp
and are not byte-reproducible. SOW keeps a signature-neutral digest of the immutable header and
payload, recognizes the retry, and reuses the object it already signed instead of producing a
second one.

### Plain mode signing

In Plain mode there is no configuration file, so authorization is explicit on the command line:

```bash
sow create /srv/repo --sign-with C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
```

`--sign-with` signs only packages that are currently unsigned. Add `--overwrite` to re-sign
everything with `rpm --resign`:

```bash
sow create /srv/repo --sign-with C811FBFBFE4031E5E2D7047904DD7F129A7B65E7 --overwrite
```

The key must be a 16, 40, or 64 hex-digit GPG key ID or fingerprint, and the private key must
already be usable by `rpm` in that environment — SOW passes the identity through the `_gpg_name`
macro and never handles your passphrase. On a host without `rpm` installed, the command stops
before touching the directory:

```console
plain: sign rpm pev2-1.22.0-1.noarch.rpm: rpm executable is required for --sign-with
```

Two argument mistakes are worth knowing:

```bash
sow create /srv/repo --sign-with ABC123
```

```console
usage error: --sign-with must be a 16, 40, or 64 hexadecimal GPG key ID/fingerprint
```

```bash
sow create /srv/repo --overwrite
```

```console
usage error: --overwrite requires --sign-with
```

Both are exit code `2`. Signing and metadata are validated together before anything is published:
if a signature fails, the directory keeps its previous state.

## Step 8: Rotate the key {#step-8-rotate-the-key}

Changing the key reference or its fingerprint marks every affected Dist dirty, because the
signer is part of what defines a built generation:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=7 dirty_dists=el9,trixie pending=0/0 locked=false
```

```bash
sow build
```

```console
{"operation":"3752151705135652397","repository":"pigsty","dists":["el9","trixie"],"desired_revision":6,"built_generation":8,"noop":false,"dirty":false}
```

```bash
gpg --verify pigsty/dists/trixie/InRelease
```

```console
gpg: Signature made Tue Aug  4 12:25:43 2026 CST
gpg:                using RSA key D856A1034A0B8BCDC20FA54F63E1D670C57DB46A
gpg: Good signature from "Pigsty Repository Signing Key <repo-2027@example.com>" [ultimate]
```

Metadata rotation is that simple because metadata is regenerated on every build. Rotating a
**package** signing key is not: re-signing changes package bytes, and a repository refuses to
hold two different byte sequences under one coordinate. Bump the release number for packages you
want re-signed, or publish the new key as an additional trusted key and let it apply to new
packages going forward.

Publish the new public key alongside the old one and give clients time to import it before you
retire the old one.

## Step 9: Enforce verification on clients

Signatures only matter if clients check them.

### dnf and yum

Publish the armored public key next to the repository, then:

{{< tabpane persist="header" >}}
{{< tab header="EL8 / EL9 / EL10" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
{{< /tab >}}
{{< tab header="Import the key" lang="bash" >}}
curl -fsSL https://repo.example.com/RPM-GPG-KEY-pigsty \
  -o /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
rpm -q gpg-pubkey --qf '%{name}-%{version}-%{release} %{summary}\n'
{{< /tab >}}
{{< /tabpane >}}

The two settings verify different things and you want both:

- `repo_gpgcheck=1` verifies `repodata/repomd.xml.asc` — the metadata chain from Step 4. Without
  it, an attacker who can rewrite the index can hide packages or downgrade you to an old one.
- `gpgcheck=1` verifies the signature inside each `.rpm` — the package chain from Step 7. This
  requires package signing to be configured; with `mode: never` your packages carry whatever
  signature they arrived with, and unsigned ones will be refused.

Turn on `repo_gpgcheck` as soon as metadata signing is live. Turn on `gpgcheck` once package
signing is in place, or when every package you publish already carries a signature the client
trusts.

Verified against AlmaLinux 8, 9, and 10 with both flags enabled.

### apt

APT verifies the signed `Release`; per-package trust follows from the SHA-256 in the index.

{{< tabpane persist="header" >}}
{{< tab header="deb822" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Signed-By: /etc/apt/keyrings/pigsty.asc
{{< /tab >}}
{{< tab header="Legacy sources.list" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [signed-by=/etc/apt/keyrings/pigsty.asc] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< tab header="Install the key" lang="bash" >}}
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://repo.example.com/RPM-GPG-KEY-pigsty \
  -o /etc/apt/keyrings/pigsty.asc
chmod 0644 /etc/apt/keyrings/pigsty.asc
apt update
{{< /tab >}}
{{< /tabpane >}}

`Signed-By` scopes the key to this one repository, which is why it replaced `apt-key add` — a key
added globally could vouch for any source on the system. Use the armored `.asc` directly;
modern APT accepts it without dearmoring.

Verified against Debian 13 with apt 3.0.3 and Debian 12 with apt 2.6.1.

{{% alert title="Remove the escape hatches" color="warning" %}}
If you followed [Build an APT Repository](/docs/tutorial/apt-repo/) with `Trusted: yes` or
`trusted=yes`, delete those lines now. They disable verification entirely, and leaving one behind
silently undoes everything in this tutorial.
{{% /alert %}}

## Where to go next

{{< doc-cards cols="2" >}}
{{< doc-card title="Signing Model" link="/docs/feature/signing/" >}}
How the two trust chains are implemented, why the signer enters the built configuration digest,
and what re-signing does to package identity.
{{< /doc-card >}}
{{< doc-card title="Serve Repositories" link="/docs/tutorial/serving/" >}}
Publish the signed tree and copy it to hosts that cannot reach the build machine.
{{< /doc-card >}}
{{< doc-card title="sow.yml Reference" link="/docs/reference/config/" >}}
Every signing field, the key reference grammar, and the full configuration schema.
{{< /doc-card >}}
{{< doc-card title="Observability & Audit" link="/docs/feature/audit/" >}}
Which build signed which generation, and how to export the record.
{{< /doc-card >}}
{{< /doc-cards >}}
