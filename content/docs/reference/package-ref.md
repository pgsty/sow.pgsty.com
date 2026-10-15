---
title: "Package References"
linkTitle: "Package References"
description: "Select packages by digest, coordinate, filename, or name, and resolve ambiguous matches."
categories: [Reference]
tags: [cli, rpm, deb]
url: "/docs/reference/package-ref/"
weight: 300
icon: fa-solid fa-fingerprint
---

`rm`, `show`, and `where` accept package references. `add` accepts file or directory paths.
Use `sow ls` to find a package coordinate or SHA-256, then pass it to another command.

```bash
sow ls -r demo -d el9
sow show 'rpm:example-0:1.0-1.x86_64' -r demo
```

<span id="the-five-forms" data-td-print-local></span>
<span id="content-digest" data-td-print-local></span>
<span id="rpm-coordinate" data-td-print-local></span>
<span id="deb-coordinate" data-td-print-local></span>
<span id="filename" data-td-print-local></span>
<span id="what-does-not-work" data-td-print-local></span>

## Accepted forms

| Form | Syntax | Matches |
|---|---|---|
| SHA-256 | `sha256:<64 lowercase hex digits>` | Stored package bytes |
| RPM coordinate | `rpm:<name>-<epoch>:<version>-<release>.<arch>` | Complete RPM identity, including epoch |
| DEB coordinate | `deb:<name>=<version>:<arch>` | Complete DEB identity |
| Filename | `example-1.0-1.x86_64.rpm` | Stored package filename |
| Bare name | `example` | Binary package name |

SHA-256 values must be complete and lowercase. Abbreviations and uppercase digests are
rejected with exit `6`. The digest is for the stored bytes; Managed RPM signing can make
it different from the input file's digest.

RPM coordinates always include an epoch, using `0` when the package has none.
A reference with the `rpm:` prefix is matched against the complete stored coordinate.
Include every coordinate component to match the package.

DEB coordinates include the complete Debian version, with any epoch and revision, plus
the native architecture. Use `amd64`, `arm64`, or `all` for DEB and `x86_64`, `aarch64`,
or `noarch` for RPM. These values come from the package, not the configuration aliases.

```bash
sow where 'rpm:example-0:1.0-1.noarch'
sow where 'deb:example=2:1.0-1:amd64'
```

A filename is a convenience, not a unique identifier. Use a coordinate or full digest in
scripts. References do not support paths, globs, regular expressions, or version ranges.

<span id="bare-name" data-td-print-local></span>

## Name matching and ambiguity

| Command | Bare name matching several versions or architectures |
|---|---|
| `rm` | Removes all matching memberships in the selected Dists |
| `show` | Rejects the ambiguous reference and lists candidates |
| `where` | Requires one package identity; returns all repository locations for that identity |

Preview a name-wide removal before applying it:

```bash
sow rm example -r demo -d el9 --check
```

For `show` or `where`, select a coordinate or digest from the candidate list.
`where` can return several repositories when they contain the same format, coordinate,
and SHA-256. If repositories contain different versions or bytes for the reference,
use `-r` or a more specific reference.

Other reference forms must identify one object within a repository. A missing or
ambiguous reference returns exit `6`.

<span id="scope" data-td-print-local></span>

## Search scope

`rm` and `where` search Desired membership. Without `-d`, `show` searches all recorded
package objects, including packages that no longer belong to a Dist. With `-d`, it searches
Desired membership in those Dists. Unrecorded files are not query results.

| Command | Default scope | Selection |
|---|---|---|
| `rm` | Selected Dists of one repository | `-r`; repeatable `-d`, or inferred Dist |
| `show` | All recorded package objects in one repository | `-r`; optional `-d` limits to Desired membership |
| `where` | All repositories in the workspace | Optional `-r` and `-d` |

For `rm`, if the Dist cannot be inferred and the repository has several Dists, supply
`-d`. Without `-r`, `where -d NAME` searches repositories containing that Dist name.
It reports an error if the requested Dist name exists nowhere.

<span id="coordinates-and-identity" data-td-print-local></span>

## Coordinate conflicts

Within a repository, one coordinate identifies at most one content object. SOW rejects
a different package with an existing coordinate and does not replace it silently.
Changing only a signature still changes the exact-byte identity.

With active RPM signing, SOW can reuse an existing signed object when its coordinate,
signature-neutral payload, and signing policy match. Otherwise, use a new release and
filename for changed bytes. See [Signing](/docs/feature/signing/).

See [`rm`](/docs/command/rm/), [`show`](/docs/command/show/), and
[`where`](/docs/command/where/) for command options.

<span id="see-also" data-td-print-local></span>
