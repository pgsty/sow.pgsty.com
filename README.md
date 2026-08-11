# SOW Docs

This repository contains the bilingual docs for **SOW**, the self-contained
APT / YUM package repository manager by [Pigsty](https://pigsty.io). It uses
[Hugo](https://gohugo.io/) and the [OINK](https://github.com/pgsty/oink) docs
theme, with English at `/` and Simplified Chinese at `/zh/`.

- Site: <https://sow.pgsty.com>
- Project: <https://github.com/pgsty/sow>

## Layout

```
content/
  _index.md            # landing page metadata
  docs/                # docs, one .md (en) + one .zh.md (zh) per page
    start/             # Get Started
    tutorial/          # task-oriented walkthroughs
    feature/           # explanation: how SOW works
    design/            # maintained architecture, invariants, and compatibility boundaries
    command/           # complete command reference
    reference/         # sow.yml, layouts, exit codes, compatibility
  blog/                # release notes and announcements
data/home/{en,zh}.yaml # OINK landing-page structure and bilingual copy
data/releases/sow.yaml # release blueprint and publication switch
layouts/download/     # SOW-specific download content inside the OINK shell
assets/scss/          # minimal SOW download-page styles
```

OINK owns the common docs/blog shell, navigation, search, content blocks, and core
shortcodes. Keep site-level layouts limited to SOW-specific behavior; do not copy common
OINK or Docsy templates into this repository.

## Theme dependency

OINK 0.2.0 is imported as a Hugo Module in `hugo.yaml` and pinned in `go.mod`. The homepage is
composed by OINK from bilingual data. Docs and blog pages also render through the theme;
the site keeps only product-specific data and templates.

The intentional site-level template surface is:

- `data/home/{en,zh}.yaml` for the OINK landing page and footer;
- `layouts/download/single.html` for release assets and installation choices;
- `layouts/robots.txt` for the deployment-specific crawler policy.

All docs/blog base templates, navigation, table of contents, search, Markdown/LLMS and
print outputs, and content shortcodes resolve from OINK.

For local theme development, connect the sibling OINK checkout with the debug
shortcut. It creates or refreshes an ignored Go workspace and lets Hugo select
an available preview port:

```bash
make d
```

## Local development

Install Hugo Extended 0.160.1 or newer, Go, and Git, then run the local server:

```bash
make s
```

Build the static site with:

```bash
make b
```

Run the module verification and warning-strict production build with:

```bash
make c
```

The corresponding long targets are `debug`, `serve`, `build`, and `check`;
`make dev` retains the pinned-theme preview. Do not run `go mod tidy`: OINK is a Hugo
Module rather than an imported Go package, so `tidy` would remove the required theme pin.

The build is Hugo-only: OINK ships its styles, scripts, fonts, search, and content
runtimes with the theme, so this repository has no Node.js or CDN build dependency.

## Writing conventions

- Every page ships as an English `.md` / Chinese `.zh.md` pair with aligned content.
- Front matter must set an explicit `url:` (Chinese pages carry the `/zh/` prefix).
- Command transcripts are real executions against the repository-matched `sow` binary; do not
  invent output.
- This repository is the authority for maintained SOW user and design documentation.

## License

Unless otherwise noted, the docs and original site content in this repository
are licensed under the [Creative Commons Attribution 4.0 International License][cc-by-4].
See [LICENSE](LICENSE) for the complete legal code. Third-party software and assets retain
their respective licenses; OINK itself is licensed under Apache License 2.0.

[cc-by-4]: https://creativecommons.org/licenses/by/4.0/
