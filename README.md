# SOW Documentation

This repository contains the bilingual documentation for **SOW**, the self-contained
APT / YUM package repository manager by [Pigsty](https://pigsty.io). It uses
[Hugo](https://gohugo.io/) and [Docsy](https://www.docsy.dev/), with English at `/`
and Simplified Chinese at `/zh/`.

- Site: <https://sow.pgsty.com>
- Project: <https://github.com/pgsty/sow>

## Layout

```
content/
  _index.md            # landing page metadata (page rendered by layouts/index.html)
  docs/                # documentation, one .md (en) + one .zh.md (zh) per page
    start/             # getting started
    tutorial/          # task-oriented walkthroughs
    feature/           # explanation: how SOW works
    design/            # maintained architecture, invariants, and compatibility boundaries
    reference/         # CLI, sow.yml, layouts, exit codes, compatibility
  blog/                # release notes and announcements
data/docs_nav.json     # generated sidebar tree — do not edit by hand
```

The docs sidebar is rendered from `data/docs_nav.json`. Regenerate it after adding,
removing, or re-weighting any page under `content/docs/`:

```bash
python3 bin/gen_docs_nav.py
```

## Local development

Install Hugo Extended, Go, Node.js, and npm. Install the pinned PostCSS toolchain
once, then run the local server:

```bash
npm ci
make dev
```

Build the static site with:

```bash
make build
```

Run the module verification and warning-strict production build with:

```bash
make check
```

Docsy is pinned as a Hugo Module. Project-specific layouts and SCSS extend the theme
without vendoring its source.

## Writing conventions

- Every page ships as an English `.md` / Chinese `.zh.md` pair with aligned content.
- Front matter must set an explicit `url:` (Chinese pages carry the `/zh/` prefix).
- Command transcripts are real executions against the current `sow` binary; do not
  invent output.
- This repository is the authority for maintained user and design documentation for the
  current SOW release.
