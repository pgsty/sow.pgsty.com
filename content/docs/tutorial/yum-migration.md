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

<span id="1-establish-the-migration-boundary" data-td-print-local></span>

## 1. Prepare a working copy

Back up the current packages and metadata. Make a separate working copy for the migration; copy RPM files without hard links if you plan to re-sign them. Check the installed binary:

```bash
SOW="$(command -v sow)"
"$SOW" version
```

Confirm that the version is 0.5.0 or later.

| Check | Action |
|---|---|
| Package layout | Plain reads top-level regular RPMs; migrate nested package layouts separately |
| Client features | Plain emits primary/filelists/other XML, not SQLite databases or module streams |
| Package trust | Keep valid upstream signatures, or deliberately replace them with your own key |
| Index trust | If clients use `repo_gpgcheck=1`, sign and verify the new `repomd.xml` separately |
| Existing clients | Include clients with cached metadata, using their existing URL and repository ID |

If your clients use modular filtering, keep the repository's existing `module_hotfixes=1` setting where needed. Plain metadata does not include module streams or profiles.

## 2. Preserve publication history

EL7 YUM can reject an index whose largest data timestamp is older than the cached index. Read `<data><timestamp>` in the current `repomd.xml` and retained copies, then use the largest value clients may have seen. If the live index was reset to zero, recover that value from earlier copies or publication records. Use data timestamps, not `revision` or file modification times.

Have the maintenance script serialize updates and save the greatest published timestamp outside the served tree. For changed content, choose:

```text
next time = max(current Unix second, largest known publication time + 1)
```

Save the chosen timestamp before switching the public index. A failed publication may leave a gap in the sequence. Keep this record when you restore old content or move the repository to another directory. The `+1` distinguishes publications; EL7 also accepts equal timestamps.

For unchanged content, reuse the timestamp after checking the indexes, referenced checksums, and signature. Repair a zero or regressed timestamp. Passing the current time on every run changes `repomd.xml`, so `create` can no longer report a no-op.

## 3. Build and sign a candidate

For this one-off example, prepare `/srv/yum.candidate` as an independent copy.
Set `HISTORICAL_MAX` to the verified maximum from the live index, the saved maximum publication time, and trusted history.
Set `SIGN_KEY` to the full fingerprint of your metadata signing key.
The following commands use Python 3 to choose a strictly newer time:

```bash
set -euo pipefail
: "${SOW:?Set the path to the tested SOW binary}"
: "${HISTORICAL_MAX:?Set the verified historical maximum Unix second}"
: "${SIGN_KEY:?Set the full metadata signing fingerprint}"
PUBLISH_TIME=$(python3 -c 'import sys,time; h=int(sys.argv[1]); assert 0 <= h < 253402300799; print(max(int(time.time()), h+1))' "$HISTORICAL_MAX")

"$SOW" create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
gpg --batch --yes --armor --detach-sign --local-user "$SIGN_KEY" \
  --output /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
gpg --verify /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
```

Record `PUBLISH_TIME` in the maintenance system before publishing the candidate. Compare the fingerprint from `gpg --verify` with the expected signing key.

`--sign-with KEY` signs unsigned RPMs and preserves existing signatures, including vendor signatures. To replace every package signature with your key, add `--overwrite` in the candidate copy. This changes package bytes; `create` builds indexes from the signed result. Generate the detached index signature after the final `create` run.

<span id="4-verify-before-promotion" data-td-print-local></span>

## 4. Test the candidate

Point a test client's original repository URL at the candidate directory. Keep its old
cache, repository ID, and signature settings. Refresh the index, then download and
install a package. This checks cache compatibility, package paths, and signatures.

If you are migrating an automated update script, also check two cases:

1. With the same inputs, options, and timestamp, a repeat build reports `noop=true`.
   Preserve the existing valid detached signature.
2. After package content changes, the script advances the timestamp and the same client
   can fetch the new package.

When comparing with `createrepo_c`, check dependency meaning and client behavior; XML
formatting can differ. See [Platforms & Integrations](/docs/reference/compatibility/).

<span id="5-promote-and-retain-recovery-material" data-td-print-local></span>

## 5. Publish the repository

Plain replaces multiple files; it does not make the whole directory switch atomically.
Coordinate package replacement, metadata, detached signatures, and cache visibility in
your publication layer. Retain metadata objects that cached clients may still request;
raw Plain rebuilds may remove old SOW checksum-named metadata from the directory.

Keep the original backup and the saved maximum publication time. Roll back package content by rebuilding
and signing it as a newer publication. Restoring an old `repomd.xml` beside changed RPMs
can reintroduce checksum or timestamp failures.

Use the checks above for Plain repositories; `sow check` applies to Managed repositories. See [`sow create`](/docs/command/create/) for options and [Signing](/docs/tutorial/signing/) for package and metadata signatures.
