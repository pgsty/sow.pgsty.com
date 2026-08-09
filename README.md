# SOW Documentation

This repository contains the bilingual documentation for **SOW**, the self-contained
APT / YUM package repository manager by [Pigsty](https://pigsty.io). It uses
[Hugo](https://gohugo.io/) and the [OINK](https://github.com/pgsty/oink) documentation
theme, with English at `/` and Simplified Chinese at `/zh/`.

- Site: <https://sow.pgsty.com>
- Project: <https://github.com/pgsty/sow>

## Layout

```
content/
  _index.md            # landing page metadata
  docs/                # documentation, one .md (en) + one .zh.md (zh) per page
    start/             # getting started
    tutorial/          # task-oriented walkthroughs
    feature/           # explanation: how SOW works
    design/            # maintained architecture, invariants, and compatibility boundaries
    command/           # complete command manual
    reference/         # sow.yml, layouts, exit codes, compatibility
  blog/                # release notes and announcements
data/home/metrics.yaml # repository facts used by the custom landing page
layouts/index.html     # SOW-specific landing page; docs/blog come from OINK
```

OINK owns the common docs/blog shell, navigation, search, content blocks, and core
shortcodes. Keep site-level layouts limited to SOW-specific behavior; do not copy common
OINK or Docsy templates into this repository.

## Theme dependency

OINK is imported as a Hugo Module in `hugo.yaml` and pinned in `go.mod`. The site keeps
its product landing page, homepage search index, and product assets, while ordinary
documentation and blog pages render directly through the theme.

The intentional site-level template surface is:

- `layouts/index.html` and `layouts/_partials/home/sow-footer.html` for the landing page;
- `layouts/_default/index.json` and `layouts/_partials/sow/` for landing-page search;
- `layouts/robots.txt` for the deployment-specific crawler policy.

All docs/blog base templates, navigation, table of contents, search, Markdown/LLMS and
print outputs, and content shortcodes resolve from OINK.

For local theme development, connect a sibling OINK checkout with an ignored Go
workspace:

```bash
go work init .
go work edit -replace=github.com/pgsty/oink=../oink
HUGO_MODULE_WORKSPACE=go.work make dev
```

## Local development

Install Hugo Extended 0.160.1 or newer, Go, and Git, then run the local server:

```bash
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

The build is Hugo-only: OINK ships its styles, scripts, fonts, search, and content
runtimes with the theme, so this repository has no Node.js or CDN build dependency.

## Writing conventions

- Every page ships as an English `.md` / Chinese `.zh.md` pair with aligned content.
- Front matter must set an explicit `url:` (Chinese pages carry the `/zh/` prefix).
- Command transcripts are real executions against the current `sow` binary; do not
  invent output.
- This repository is the authority for maintained user and design documentation for the
  current SOW release.

## License

Unless otherwise noted, the documentation and original site content in this repository
are licensed under the [Creative Commons Attribution 4.0 International License][cc-by-4].
See [LICENSE](LICENSE) for the complete legal code. Third-party software and assets retain
their respective licenses; OINK itself is licensed under Apache License 2.0.

[cc-by-4]: https://creativecommons.org/licenses/by/4.0/
