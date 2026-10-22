---
title: "Download SOW"
linkTitle: "Download"
description: "Install SOW from the Pigsty repository, a pinned RPM or DEB package, a Linux or macOS archive, or a source build. Check downloaded files with the release SHA-256 digests."
url: "/download/"
weight: 20
icon: fa-solid fa-download
layout: landing
landing: download
translationKey: download
categories: [Download]
tags: [install, rpm, deb, release]
search_keywords: [download, install, package, RPM, DEB, YUM, APT, archive, tarball, checksum, SHA256, Pigsty, source]
search_boost: 1.5
---

<!-- The landing layout renders `data/landing/download/<lang>.yaml`, not this
     body. The paragraph below is the page's searchable text: OINK's offline
     index skips a page with no raw content, and this is a top-level navigation
     entry that readers look for by artifact name. -->

Install SOW from the Pigsty infra repository with `apt install sow` or `dnf install sow`,
from a pinned RPM or DEB package, from a `tar.gz` archive for Linux or macOS on `amd64`
and `arm64`, or from a source build of a tagged release. SOW 0.6.1 is available. The Pigsty repository is a rolling channel. Each build provides the same CLI for its target
platform, and every published artifact carries a SHA-256 digest listed
in `SHA256SUMS`. After installing, run `sow version` and `sow help`, then point
`sow create` at a directory of packages.
