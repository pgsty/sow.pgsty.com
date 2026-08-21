#!/usr/bin/env python3
"""Generate the SOW hero architecture diagram.

Run from the repository root:  python3 bin/gen_hero_diagram.py

Emits four files into static/img -- {en, zh} x {light, dark} -- from one
template, so a palette or a label can never drift between them. The four SVGs
are checked in; regenerate them here rather than editing them by hand.

One template, two palettes: a light and a dark file that cannot drift apart.
The SVG is consumed as a CSS background-image, so it is a standalone document —
no external fonts, no CSS variables from the page. Font stacks are therefore
system stacks, and every colour is literal.
"""

from pathlib import Path

W, H = 440, 436

SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

PALETTES = {
    "light": dict(
        ink="#0d161f",
        muted="#5d7189",
        faint="#7d8ea3",
        line="rgba(48,74,105,0.22)",
        card="#ffffff",
        card_alt="#f6f9fc",
        teal="#0d7f77",
        teal_fill="rgba(20,184,166,0.16)",
        teal_line="rgba(13,127,119,0.45)",
        copper="#a96c26",
        copper_fill="rgba(180,118,46,0.16)",
        copper_line="rgba(180,118,46,0.48)",
        blue="#245f94",
        blue_fill="rgba(36,95,148,0.13)",
        blue_line="rgba(36,95,148,0.42)",
        arrow="rgba(48,74,105,0.46)",
    ),
    "dark": dict(
        ink="#f4f8fc",
        muted="#93a3b8",
        faint="#7f8da1",
        line="rgba(148,176,210,0.24)",
        card="#121c29",
        card_alt="#182435",
        teal="#5eead4",
        teal_fill="rgba(94,234,212,0.15)",
        teal_line="rgba(94,234,212,0.42)",
        copper="#e0a35c",
        copper_fill="rgba(224,163,92,0.15)",
        copper_line="rgba(224,163,92,0.42)",
        blue="#5da2dd",
        blue_fill="rgba(93,162,221,0.14)",
        blue_line="rgba(93,162,221,0.40)",
        arrow="rgba(148,176,210,0.48)",
    ),
}


LOCALES = {
    "en": dict(
        cjk=False,
        inputs="LOCAL PACKAGE FILES",
        pool="PACKAGE POOL",
        pool_note="stored once",
        pool_caption="one object per package \u00b7 no duplicate keys",
        views="REPOSITORY VIEWS",
        views_note="metadata only",
        el="EL 8 / 9 / 10",
        publish="INCREMENTAL PUBLISH",
        publish_note="verified",
        delta="changed objects only",
        targets="filesystem \u00b7 S3 / R2",
        title=("SOW pipeline: local RPM and DEB files enter one deduplicated package pool, "
               "which is projected as YUM and APT repository views and published as a delta"),
    ),
    "zh": dict(
        cjk=True,
        inputs="\u672c\u5730\u8f6f\u4ef6\u5305\u6587\u4ef6",
        pool="\u7edf\u4e00\u5305\u6c60",
        pool_note="\u53ea\u5b58\u4e00\u4efd",
        pool_caption="\u6bcf\u4e2a\u8f6f\u4ef6\u5305\u4e00\u4e2a\u5bf9\u8c61 \u00b7 \u65e0\u91cd\u590d object key",
        views="\u4ed3\u5e93\u89c6\u56fe",
        views_note="\u4ec5\u5143\u6570\u636e",
        el="EL 8 / 9 / 10",
        publish="\u589e\u91cf\u53d1\u5e03",
        publish_note="\u5df2\u6821\u9a8c",
        delta="\u53ea\u4e0a\u4f20\u53d8\u66f4\u5bf9\u8c61",
        targets="\u6587\u4ef6\u7cfb\u7edf \u00b7 S3 / R2",
        title=("SOW \u5de5\u4f5c\u65b9\u5f0f\uff1a\u672c\u5730 RPM \u4e0e DEB \u6587\u4ef6\u8fdb\u5165\u7edf\u4e00\u5305\u6c60\uff0c"
               "\u5305\u6c60\u518d\u6295\u5f71\u4e3a\u53ea\u542b\u5143\u6570\u636e\u7684 YUM \u4e0e APT \u4ed3\u5e93\u89c6\u56fe\uff0c"
               "\u53d1\u5e03\u65f6\u53ea\u4e0a\u4f20\u53d1\u751f\u53d8\u5316\u7684\u5bf9\u8c61"),
    ),
}


def text(x, y, s, fill, size, weight=600, anchor="middle", family=SANS, ls=None):
    ls_attr = f' letter-spacing="{ls}"' if ls else ""
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{family}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}"{ls_attr}>{s}</text>'
    )


def eyebrow(x, y, s, fill, anchor="start", cjk=False):
    """Stage label. CJK has no monospace tradition for this, and wide tracking
    hurts rather than helps it, so the Chinese build uses the sans stack."""
    if cjk:
        return text(x, y, s, fill, 11, weight=700, anchor=anchor, family=SANS, ls=1.2)
    return text(x, y, s, fill, 10, weight=600, anchor=anchor, family=MONO, ls=1.7)


def box(x, y, w, h, rx, fill, stroke, sw=1.25):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    )


def link(points, color, head=True):
    """A polyline connector, with one arrowhead at the final point."""
    d = " ".join(f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    out = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5" '
           f'stroke-linecap="round" stroke-linejoin="round"/>']
    if head:
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / n, dy / n
        hl, hw = 7.0, 3.8
        bx, by = x2 - ux * hl, y2 - uy * hl
        px, py = -uy, ux
        out.append(
            f'<path d="M {x2:.1f} {y2:.1f} L {bx + px * hw:.1f} {by + py * hw:.1f} '
            f'L {bx - px * hw:.1f} {by - py * hw:.1f} Z" fill="{color}"/>'
        )
    return "".join(out)


def build(p, t):
    cjk = t["cjk"]
    o = []
    a = o.append

    # ---- Inputs: the files already sitting on the box ------------------------
    a(eyebrow(220, 14, t["inputs"], p["muted"], anchor="middle", cjk=cjk))
    a(box(78, 24, 126, 36, 10, p["copper_fill"], p["copper_line"]))
    a(box(236, 24, 126, 36, 10, p["blue_fill"], p["blue_line"]))
    a(text(141, 48, ".rpm", p["copper"], 15, 700, family=MONO))
    a(text(299, 48, ".deb", p["blue"], 15, 700, family=MONO))

    # Both inputs meet on one trunk before they reach the pool.
    a(link([(141, 60), (141, 70), (220, 70)], p["arrow"], head=False))
    a(link([(299, 60), (299, 70), (220, 70)], p["arrow"], head=False))
    a(link([(220, 70), (220, 84)], p["arrow"]))

    # ---- Stage 1: one pool, each package body stored exactly once ------------
    a(box(32, 86, 376, 88, 14, p["card"], p["line"]))
    a(eyebrow(52, 110, t["pool"], p["teal"], cjk=cjk))
    a(text(388, 110, t["pool_note"], p["faint"], 11, 500, anchor="end"))
    kinds = ["t", "c", "t", "t", "c", "t", "c", "t", "t"]
    cw, gap = 24, 11
    x = (W - (len(kinds) * cw + (len(kinds) - 1) * gap)) / 2
    for kind in kinds:
        fill = p["teal_fill"] if kind == "t" else p["copper_fill"]
        stroke = p["teal_line"] if kind == "t" else p["copper_line"]
        a(box(round(x, 1), 126, cw, 24, 5, fill, stroke, sw=1.15))
        x += cw + gap
    a(text(220, 165, t["pool_caption"], p["muted"], 10.5, 500))

    a(link([(220, 174), (220, 196)], p["arrow"]))

    # ---- Stage 2: the repositories clients actually consume ------------------
    a(box(24, 198, 392, 116, 14, p["card"], p["line"]))
    a(eyebrow(44, 222, t["views"], p["teal"], cjk=cjk))
    a(text(396, 222, t["views_note"], p["faint"], 11, 500, anchor="end"))
    views = [
        (45, "YUM", t["el"], p["copper"], p["copper_fill"], p["copper_line"]),
        (167, "APT", "Debian", p["blue"], p["blue_fill"], p["blue_line"]),
        (289, "APT", "Ubuntu", p["blue"], p["blue_fill"], p["blue_line"]),
    ]
    for vx, kind, dist, fg, fill, stroke in views:
        a(box(vx, 236, 106, 62, 11, fill, stroke))
        a(text(vx + 53, 264, kind, fg, 16, 700, family=MONO))
        a(text(vx + 53, 285, dist, p["muted"], 10.5, 500))

    a(link([(220, 314), (220, 336)], p["arrow"]))

    # ---- Stage 3: only what changed leaves ----------------------------------
    a(box(32, 338, 376, 86, 14, p["card_alt"], p["line"]))
    a(eyebrow(52, 362, t["publish"], p["teal"], cjk=cjk))
    a(text(388, 362, t["publish_note"], p["faint"], 11, 500, anchor="end"))
    a(f'<text x="220" y="393" text-anchor="middle" font-family="{SANS if cjk else MONO}" '
      f'font-size="{17 if cjk else 16}" font-weight="700" fill="{p["ink"]}">'
      f'<tspan fill="{p["teal"]}">\u0394</tspan> {t["delta"]}</text>')
    a(text(220, 413, t["targets"], p["muted"], 10.5, 500))

    title = t["title"]
    body = "\n  ".join(o)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img" aria-labelledby="sow-arch-title"
     shape-rendering="geometricPrecision" text-rendering="geometricPrecision">
  <title id="sow-arch-title">{title}</title>
  {body}
</svg>
"""


out = Path(__file__).resolve().parents[1] / "static/img"
for lang, strings in LOCALES.items():
    for mode, palette in PALETTES.items():
        suffix = "" if lang == "en" else f"-{lang}"
        path = out / f"sow-architecture{suffix}-{mode}.svg"
        path.write_text(build(palette, strings), encoding="utf-8")
        print("wrote", path.name, path.stat().st_size, "bytes")
