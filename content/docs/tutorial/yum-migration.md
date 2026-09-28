---
title: "Migrate an Existing YUM Repository"
linkTitle: "Migrate YUM"
description: "Move a flat RPM repository to SOW while preserving client cache compatibility, package trust, and publication time."
categories: [Tutorial]
tags: [yum, plain, migration, signing]
url: "/docs/tutorial/yum-migration/"
weight: 150
icon: fa-solid fa-arrows-rotate
---

This guide covers a flat directory of RPMs and `repodata/`, such as a repository previously
built with `createrepo_c`. It uses Plain `sow create`, without creating a Managed workspace.
The publication-time option requires **SOW 0.5.0 or later**.

## 1. Establish the migration boundary

Use a candidate copy and retain a complete backup of the previous packages and metadata.
Do not use hard links for RPMs that may be re-signed. First check the exact binary:

```bash
SOW=/path/to/sow
"$SOW" version
"$SOW" create --help
```

The help must list `--metadata-timestamp`. A 0.4.0 release binary does not accept it.

| Check | Required decision |
|---|---|
| Package layout | Plain reads top-level regular RPMs; migrate nested package layouts separately |
| Client features | Plain emits primary/filelists/other XML, not SQLite databases or module streams |
| Package trust | Keep valid upstream signatures, or deliberately replace them with your own key |
| Index trust | If clients use `repo_gpgcheck=1`, sign and verify the new `repomd.xml` separately |
| Existing clients | Include clients with cached metadata, using their existing URL and repository ID |

For ordinary RPMs in an environment with modular filtering, retain an appropriate
`module_hotfixes=1` policy. This does not recreate `dnf module install` streams or profiles.

## 2. Preserve publication history

EL7 YUM can reject an index whose largest data timestamp is older than its cached index.
Read the `<data><timestamp>` values in the current `repomd.xml` and trusted earlier copies.
Use the largest value clients may have seen. If the live index was already reset to zero,
it is not a sufficient record of that history. Revision and file mtime are not substitutes.

A maintenance wrapper should hold one lock for the repository and retain a publication
high-water mark outside the uploaded tree. For a changed generation, choose:

```text
next time = max(current Unix second,
                largest live index time + 1,
                retained high-water mark + 1,
                trusted historical lower bound + 1)
```

Persist the chosen high-water mark before switching the public index. A failed publication
may consume a timestamp; skipping a value is harmless. Keep the clock when restoring old
content or moving the repository to another local path serving the same public URL.

For an unchanged generation, a wrapper may reuse the existing index and detached signature
after checking the full metadata content identity, referenced checksums, and signature. A
zero or regressed timestamp still requires repair. Passing a fresh time on every invocation
of raw `create` changes the index and defeats its no-op behavior.

## 3. Build and sign a candidate

For this one-off example, prepare `/srv/yum.candidate` as an independent copy. Set
`HISTORICAL_MAX` to the verified maximum from the live index, persistent clock, and trusted
history; set `SIGN_KEY` to the full fingerprint of your metadata signing key. The following
commands use Python 3 to choose a strictly newer time:

```bash
set -euo pipefail
: "${SOW:?Set the path to the tested SOW binary}"
: "${HISTORICAL_MAX:?Set the verified historical maximum Unix second}"
: "${SIGN_KEY:?Set the full metadata signing fingerprint}"
PUBLISH_TIME=$(python3 -c 'import sys,time; h=int(sys.argv[1]); assert 0 <= h < 9223372036854775807; print(max(int(time.time()), h+1))' "$HISTORICAL_MAX")

"$SOW" create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
gpg --batch --yes --armor --detach-sign --local-user "$SIGN_KEY" \
  --output /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
gpg --verify /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
```

This generates a candidate; it does not save the persistent clock or publish the directory.
Record `PUBLISH_TIME` using your maintenance system before promotion. Verify the signature
against the intended public key, not merely any key present in a broad trust store.

`--sign-with KEY` only fills unsigned RPMs. It preserves already signed packages, including
packages signed by another vendor. If the intended policy is that every RPM is signed by
your key, verify every package against that key and selectively re-sign mismatches in the
candidate. `--overwrite` is the explicit bulk alternative: it re-signs every retained RPM,
changes package bytes, and requires rebuilding metadata from those final bytes. Always
regenerate the detached index signature after the final `create` run.

## 4. Verify before promotion

Check the following on the candidate and the intended serving endpoint:

1. The three XML streams match the RPM set and their referenced checksums. If only the
   publication time changed, RPMs and compressed XML should be byte-identical.
2. Every package and metadata signature satisfies the intended client trust policy.
3. A repeated metadata build with the same package bytes, options, and timestamp reports
   a no-op; do not force re-signing for this check. A wrapper
   should also preserve the existing valid detached signature instead of re-signing it.
4. A client with the previous cached index accepts the new index, then downloads and
   verifies a package. Keep the same URL/repository ID and the cache for this test.
5. A second content update advances the timestamp and reaches that same client. If install
   behavior matters, include an installation on a disposable host with the exact client.

For an existing signed repository, retain `gpgcheck=1` and `repo_gpgcheck=1` throughout
acceptance. Clearing the cache or disabling signature checks would omit the behavior being
tested. Compare dependency meaning rather than requiring XML to be byte-identical to an
older createrepo_c release; see [Platforms & Integrations](/docs/reference/compatibility/).

## 5. Promote and retain recovery material

Plain replaces multiple files; it does not make the whole directory switch atomically.
Coordinate package replacement, metadata, detached signatures, and cache visibility in
your publication layer. Retain metadata objects that cached clients may still request;
raw Plain rebuilds may remove old SOW checksum-named metadata from the directory.

Keep the original backup and the persistent clock. Roll back package content by rebuilding
and signing it as a newer publication. Restoring an old `repomd.xml` beside changed RPMs
can reintroduce checksum or timestamp failures.

Managed `sow check` does not audit a Plain directory. Its acceptance comes from the checks
above and the actual YUM/DNF client. See [`sow create`](/docs/command/create/) for the exact
command contract and [Signing](/docs/tutorial/signing/) for the two signature layers.
