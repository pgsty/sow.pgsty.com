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
    command/           # complete command reference
    reference/         # sow.yml, layouts, exit codes, compatibility
  blog/
    design/            # dated architecture decisions and rationale
    release/           # release notes and announcements
data/home/{en,zh}.yaml # OINK landing-page structure and bilingual copy
data/download/sow.yaml            # install channels, assets, and release switch
data/landing/download/{en,zh}.yaml # bilingual download-page composition
layouts/_partials/                # narrow SOW-specific theme extensions
assets/scss/                      # minimal SOW download-page styles
```

OINK owns the common docs/blog shell, navigation, search, content blocks, and core
shortcodes. Keep site-level layouts limited to SOW-specific behavior; do not copy common
OINK or Docsy templates into this repository.

## Theme dependency

OINK 1.2.0 is imported as a Hugo Module in `hugo.yaml` and pinned in `go.mod`. The homepage is
composed by OINK from bilingual data. Docs and blog pages also render through the theme;
the site keeps only product-specific data and templates.

The intentional site-level template surface is:

- `data/home/{en,zh}.yaml` for the OINK landing page;
- `data/footer/{en,zh}.yaml` for the shared footer;
- `data/download/sow.yaml` and `data/landing/download/{en,zh}.yaml` for release
  assets and installation choices;
- `layouts/_partials/sow/content-section.html` and
  `layouts/_partials/page-meta-lastmod.html` for the two site-specific rendering hooks;
- `layouts/robots.txt` for the deployment-specific crawler policy.

All docs/blog base templates, navigation, table of contents, search, Markdown/LLMS and
print outputs, and content shortcodes resolve from OINK.

For local theme development, connect the sibling OINK checkout with the debug
shortcut. It sets an inline module replacement for that command and lets Hugo
select an available preview port without creating or changing a Go workspace:

```bash
make d
```

## Local development

Install Hugo Extended 0.160.1 or newer, Go 1.27.0 or newer, and Git, then run the local server:

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
`make dev` uses the sibling OINK checkout while `make serve` retains the pinned-theme preview. Do not run `go mod tidy`: OINK is a Hugo
Module rather than an imported Go package, so `tidy` would remove the required theme pin.

The build is Hugo-only: OINK ships its styles, scripts, fonts, search, and content
runtimes with the theme, so this repository has no Node.js or CDN build dependency.

## Writing conventions

This repository maintains SOW's user and design documentation. Use the writing rules of
[ASD-STE100](https://www.asd-ste100.org/about_STE.html), with SOW terms for software concepts.
Use natural Chinese with the same meaning and sequence.

- Start with the task and its result. Present the normal workflow before alternatives.
- Introduce concepts when the reader needs them. Explain what changes, what to do next, and why.
- Use complete, active sentences. Keep necessary articles and connecting words.
- In English, use at most 20 words per instruction and 25 words per descriptive sentence.
- Give one instruction per sentence. Put conditions before the action and explanations outside the steps.
- Keep each paragraph on one topic. Remove repetition that adds no action or explanation.
- Use one term for each concept. In Chinese, use 工作区, 仓库, 包池, and 构建快照（Generation）.
  Keep command and field names unchanged. Dist is a named package set; Desired and Built identify its selected and built states.
- Keep local builds, HTTP serving, and target publication distinct. Put a limit next to the operation it affects.
- Use sentence case in English headings. Prefer concrete verbs to abstract nouns.

## Content maintenance

- Update English `.md` and Chinese `.zh.md` pages together. Set explicit `url:` values, with `/zh/` for Chinese.
- Preserve existing heading anchors when renaming sections. Keep historical release facts tied to their tags.
- Verify commands, defaults, configuration, and examples against SOW source and `sow help`.
  Use actual output from the matching binary for command transcripts.
- At release updates, set `params.version` and update the homepage and download notes.
  Copy the published `SHA256SUMS` to `assets/release/sow-checksums.txt`. Check that all listed filenames match the release.
- Keep whitespace around strong-emphasis delimiters next to Chinese prose.
  Run `make check` to check Markdown, modules, the production build, and internal links.

## License

Unless otherwise noted, the docs and original site content in this repository
are licensed under the [Creative Commons Attribution 4.0 International License][cc-by-4].
See [LICENSE](LICENSE) for the complete legal code. Third-party software and assets retain
their respective licenses; OINK itself is licensed under Apache License 2.0.

[cc-by-4]: https://creativecommons.org/licenses/by/4.0/
