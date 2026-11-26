#!/usr/bin/env python3
"""Render the Catppuccin Macchiato info card as a self-contained SVG."""

from datetime import datetime, timezone
from xml.sax.saxutils import escape

# ── Catppuccin Macchiato palette ─────────────────────────────────────────────
ROSEWATER = "#f4dbd6"
FLAMINGO = "#f0c6c6"
PINK = "#f5bde6"
MAUVE = "#c6a0f6"
RED = "#ed8796"
MAROON = "#ee99a0"
PEACH = "#f5a97f"
YELLOW = "#eed49f"
GREEN = "#a6da95"
TEAL = "#8bd5ca"
SKY = "#91d7e3"
SAPPHIRE = "#7dc4e4"
BLUE = "#8aadf4"
LAVENDER = "#b7bdf8"
TEXT = "#cad3f5"
SUBTEXT1 = "#b8c0e0"
SUBTEXT0 = "#a5adcb"
OVERLAY2 = "#939ab7"
OVERLAY1 = "#8087a2"
OVERLAY0 = "#6e738d"
SURFACE2 = "#5b6078"
SURFACE1 = "#494d64"
SURFACE0 = "#363a4f"
BASE = "#24273a"
MANTLE = "#1e2030"
CRUST = "#181926"

PALETTE_NORMAL = [SURFACE1, RED, GREEN, YELLOW, BLUE, PINK, TEAL, SUBTEXT1]
PALETTE_BRIGHT = [OVERLAY0, MAROON, SKY, PEACH, LAVENDER, MAUVE, SAPPHIRE, TEXT]

LANG_COLORS = {
    "Python": BLUE, "Java": PEACH, "JavaScript": YELLOW, "TypeScript": SAPPHIRE,
    "Vue": GREEN, "HTML": RED, "CSS": MAUVE, "Go": TEAL, "Shell": GREEN,
    "Rust": PEACH, "C": SUBTEXT1, "C++": MAROON, "C#": MAUVE, "Ruby": RED,
    "PHP": LAVENDER, "Dart": SAPPHIRE, "SCSS": PINK, "Lua": BLUE,
    "Kotlin": PEACH, "Swift": PEACH, "Ruby": RED,
}
DEFAULT_LANG_COLOR = LAVENDER

MONO = "Menlo, Monaco, 'Courier New', monospace"

# ── Layout ───────────────────────────────────────────────────────────────────
W = 960
TITLE_H = 40
PAD = 28
CELL_W = 6.6
CELL_H = 11.5
ART_FONT = 11
INFO_ROW_H = 25


def esc(s: str) -> str:
    return escape(str(s))


def _text(x, y, s, fill, size=13, weight=None, anchor=None, mono=True, opacity=None):
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"', f'font-size="{size}"']
    if mono:
        attrs.append(f'font-family="{MONO}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    return f'<text {" ".join(attrs)}>{s}</text>'


def _truncate(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _sep(y: int, right_x: int, right_w: int) -> int:
    n = int(right_w / 7.8)
    return y + 18, _text(right_x, y, "/" * n, OVERLAY0, 13)


def _info_row(y, right_x, icon, label, value, value_fill=TEXT, value_weight=None):
    parts = [
        _text(right_x, y, icon, TEXT, 14),
        _text(right_x + 30, y, esc(label), SUBTEXT0, 13),
        _text(right_x + 150, y, esc(value), value_fill, 13, weight=value_weight),
    ]
    return y + INFO_ROW_H, parts


def _art_text(art, art_x, art_y):
    """Render the ASCII grid; spaces stay invisible on the base background."""
    out = []
    for r, row in enumerate(art):
        y = art_y + (r + 1) * CELL_H
        spans = []
        i = 0
        n = len(row)
        while i < n:
            char, color = row[i]
            if char == " ":
                spans.append(" ")
                i += 1
            else:
                j = i
                while j < n and row[j][0] != " " and row[j][1] == color:
                    j += 1
                seg = "".join(c for c, _ in row[i:j])
                spans.append(f'<tspan fill="{color}">{esc(seg)}</tspan>')
                i = j
        # trim trailing spaces
        while spans and spans[-1] == " ":
            spans.pop()
        if not spans:
            continue
        out.append(
            f'<text x="{art_x}" y="{y:.1f}" xml:space="preserve" '
            f'font-family="{MONO}" font-size="{ART_FONT}">{"".join(spans)}</text>'
        )
    return out


def render(username: str, data: dict, art: list | None) -> str:
    profile = data["profile"]
    lang_bytes = data["language_bytes"]
    total_stars = data["total_stars"]
    now = datetime.now(timezone.utc)

    name = profile.get("name") or username
    created = datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00"))
    years = (now - created).days // 365
    months = ((now - created).days % 365) // 30
    tenure = f"{years}y {months}m" if years > 0 else f"{months}m"
    joined = created.strftime("%Y-%m-%d")

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:5]
    top_total = sum(v for _, v in sorted_langs) or 1

    # ── Geometry ──
    art_cols = len(art[0]) if art else 0
    art_rows = len(art) if art else 0
    art_w = art_cols * CELL_W
    art_x = PAD
    art_y = TITLE_H + 36
    right_x = PAD + (art_w + 48 if art else 0)
    right_w = W - right_x - PAD

    parts = []
    y = TITLE_H + 26

    # Name row (big)
    parts += [
        _text(right_x, y, "👻", TEXT, 16),
        _text(right_x + 32, y, "Name", PINK, 15, weight="700"),
        _text(right_x + 150, y,
              f'{esc(name)} <tspan fill="{SUBTEXT0}">(@{esc(username)})</tspan>',
              BLUE, 15, weight="700"),
    ]
    y += 34
    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # Info rows
    info = [
        ("🌍", "Location", profile.get("location"), TEXT, None),
        ("✏️", "Bio", profile.get("bio"), SUBTEXT1, None),
        ("🏢", "Company", profile.get("company"), SUBTEXT1, None),
        ("📅", "Joined", f"{joined}  ({tenure})", BLUE, None),
        ("🔗", "Blog", profile.get("blog"), TEAL, None),
    ]
    for icon, label, value, fill, weight in info:
        if not value:
            continue
        y, row_parts = _info_row(y, right_x, icon, label, _truncate(value, 48), fill, weight)
        parts += row_parts

    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # GitHub stats strip (inline tspans)
    stats = (
        f'<tspan fill="{SUBTEXT0}">📦 </tspan><tspan fill="{BLUE}">{profile["public_repos"]}</tspan><tspan fill="{SUBTEXT0}"> repos   </tspan>'
        f'<tspan fill="{SUBTEXT0}">⭐ </tspan><tspan fill="{YELLOW}">{total_stars}</tspan><tspan fill="{SUBTEXT0}"> stars   </tspan>'
        f'<tspan fill="{SUBTEXT0}">👥 </tspan><tspan fill="{GREEN}">{profile["followers"]}</tspan><tspan fill="{SUBTEXT0}"> followers   </tspan>'
        f'<tspan fill="{SUBTEXT0}">➕ </tspan><tspan fill="{MAUVE}">{profile["following"]}</tspan><tspan fill="{SUBTEXT0}"> following</tspan>'
    )
    parts.append(_text(right_x, y, stats, SUBTEXT0, 13))
    y += 30
    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # Language distribution bars
    parts.append(_text(right_x, y, "💻", TEXT, 13))
    parts.append(_text(right_x + 26, y, "Top Languages", SUBTEXT0, 12, weight="700"))
    y += 10
    bar_x = right_x + 110
    bar_w = 260
    for lang, size in sorted_langs:
        y += 24
        pct = size / top_total * 100
        color = LANG_COLORS.get(lang, DEFAULT_LANG_COLOR)
        parts.append(_text(right_x, y, esc(lang), color, 12))
        parts.append(f'<rect x="{bar_x}" y="{y - 10}" width="{bar_w}" height="12" rx="3" fill="{SURFACE0}"/>')
        parts.append(f'<rect x="{bar_x}" y="{y - 10}" width="{max(bar_w * pct / 100, 4):.1f}" height="12" rx="3" fill="{color}"/>')
        parts.append(_text(bar_x + bar_w + 10, y, f"{pct:.1f}%", SUBTEXT0, 11))
    y += 14
    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # Palette label + swatches
    parts.append(_text(right_x, y, "🎨", TEXT, 13))
    parts.append(_text(right_x + 26, y, "Catppuccin Macchiato", SUBTEXT0, 12, weight="700"))
    y += 10
    sw = (right_w - 7 * 4) / 8
    for row_colors in (PALETTE_NORMAL, PALETTE_BRIGHT):
        y += 22
        for i, c in enumerate(row_colors):
            x = right_x + i * (sw + 4)
            parts.append(f'<rect x="{x:.1f}" y="{y - 16}" width="{sw:.1f}" height="18" rx="3" fill="{c}" stroke="{CRUST}" stroke-width="1"/>')
    content_end = y + 16

    # ── Window height ──
    art_bottom = art_y + art_rows * CELL_H if art else 0
    h = int(max(content_end, art_bottom) + 52)
    footer_y = h - 26

    # ── Assemble window chrome ──
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="GitHub stats card for @{esc(username)}">',
        f'<rect width="{W}" height="{h}" rx="12" fill="{BASE}"/>',
        f'<path d="M0,12 A12,12 0 0 1 12,0 H{W - 12} A12,12 0 0 1 {W},12 V{TITLE_H} H0 Z" fill="{MANTLE}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{CRUST}" stroke-width="1"/>',
        f'<circle cx="20" cy="20" r="6.5" fill="{RED}"/>',
        f'<circle cx="42" cy="20" r="6.5" fill="{YELLOW}"/>',
        f'<circle cx="64" cy="20" r="6.5" fill="{GREEN}"/>',
        _text(W // 2, 25, f"@{esc(username)} — stats", SUBTEXT1, 13, weight="600", anchor="middle"),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="12" fill="none" stroke="{CRUST}" stroke-width="1"/>',
    ]

    # Footer: prompt left, timestamp right
    footer_left = (
        f'<tspan fill="{GREEN}" font-weight="700">❯ </tspan>'
        f'<tspan fill="{BLUE}">{esc(username)}</tspan>'
        f'<tspan fill="{PEACH}"> [⌂ ~]</tspan>'
    )
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    footers = [
        _text(PAD, footer_y, footer_left, TEXT, 13),
        _text(W - PAD, footer_y, f"🕐 {stamp}", OVERLAY0, 11, anchor="end"),
    ]

    art_parts = _art_text(art, art_x, art_y) if art else []

    return "\n".join(head + art_parts + parts + footers + ["</svg>"])
