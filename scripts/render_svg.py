#!/usr/bin/env python3
"""Render the Catppuccin Macchiato fastfetch-style info card as SVG."""

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
    "Kotlin": PEACH, "Swift": PEACH,
}
DEFAULT_LANG_COLOR = LAVENDER

# ── Nerd Font (Font Awesome) icons ───────────────────────────────────────────
IC_USER = "\uf007"
IC_PENCIL = "\uf040"
IC_MAP = "\uf041"
IC_BRIEFCASE = "\uf0b1"
IC_CALENDAR = "\uf133"
IC_LINK = "\uf0c1"
IC_FOLDER = "\uf07b"
IC_STAR = "\uf005"
IC_USERS = "\uf0c0"
IC_CODE = "\uf121"
IC_PAINT = "\uf1fc"
IC_CLOCK = "\uf017"
IC_HOME = "\uf015"

FONT = "'JetBrainsMono Nerd Font', Menlo, Monaco, monospace"
MONO = FONT

# ── Layout (compact) ─────────────────────────────────────────────────────────
W = 860
TITLE_H = 30
PAD = 18
CELL_W = 6.0
CELL_H = 10.5
ART_FONT = 10
ART_COLS = 49
ART_ROWS = 28
ROW_H = 20
SEP_ADV = 14
BAR_H = 19


def esc(s: str) -> str:
    return escape(str(s))


def _text(x, y, s, fill, size=12, weight=None, anchor=None, mono=True, opacity=None):
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


def _sep(y: int, right_x: int, right_w: int) -> tuple[int, str]:
    n = int(right_w / 7.2)
    return y + SEP_ADV, _text(right_x, y, "/" * n, OVERLAY0, 12)


def _field(y, right_x, icon, label, value, color):
    """fastfetch-style row: icon + 'Label:' + value."""
    parts = [
        _text(right_x, y, icon, color, 12),
        _text(right_x + 22, y, f"{esc(label)}:", SUBTEXT0, 12),
        _text(right_x + 130, y, esc(value), color, 12),
    ]
    return y + ROW_H, parts


def _art_text(art, art_x, art_y):
    out = []
    for r, row in enumerate(art):
        y = art_y + (r + 1) * CELL_H
        spans = []
        i, n = 0, len(row)
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
    art_y = TITLE_H + 18
    right_x = PAD + (art_w + 34 if art else 0)
    right_w = W - right_x - PAD

    parts = []
    y = TITLE_H + 20

    # fastfetch fields
    fields = [
        (IC_USER, "Name", f"{name} (@{username})", SKY),
        (IC_MAP, "Location", profile.get("location"), TEXT),
        (IC_PENCIL, "Bio", profile.get("bio"), SUBTEXT1),
        (IC_BRIEFCASE, "Company", profile.get("company"), SUBTEXT1),
        (IC_CALENDAR, "Joined", f"{joined} ({tenure})", BLUE),
        (IC_LINK, "Blog", profile.get("blog"), TEAL),
    ]
    for icon, label, value, color in fields:
        if not value:
            continue
        y, row_parts = _field(y, right_x, icon, label, _truncate(value, 52), color)
        parts += row_parts

    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # GitHub stats as fastfetch fields
    stats = [
        (IC_FOLDER, "Repos", str(profile["public_repos"]), BLUE),
        (IC_STAR, "Stars", str(total_stars), YELLOW),
        (IC_USER, "Followers", str(profile["followers"]), GREEN),
        (IC_USERS, "Following", str(profile["following"]), MAUVE),
    ]
    for icon, label, value, color in stats:
        y, row_parts = _field(y, right_x, icon, label, value, color)
        parts += row_parts

    y, sep = _sep(y, right_x, right_w); parts.append(sep)

    # Languages: header + bars
    parts.append(_text(right_x, y, IC_CODE, TEAL, 12))
    parts.append(_text(right_x + 22, y, "Languages:", SUBTEXT0, 12))
    bar_x = right_x + 130
    bar_w = 220
    for lang, size in sorted_langs:
        y += BAR_H
        pct = size / top_total * 100
        color = LANG_COLORS.get(lang, DEFAULT_LANG_COLOR)
        parts.append(_text(bar_x, y, esc(lang), color, 11))
        bx = bar_x + 95
        parts.append(f'<rect x="{bx}" y="{y - 9}" width="{bar_w}" height="10" rx="2" fill="{SURFACE0}"/>')
        parts.append(f'<rect x="{bx}" y="{y - 9}" width="{max(bar_w * pct / 100, 4):.1f}" height="10" rx="2" fill="{color}"/>')
        parts.append(_text(bx + bar_w + 8, y, f"{pct:.1f}%", SUBTEXT0, 10))
    y += 12
    content_end = y + 10

    # ── Window height ──
    art_bottom = art_y + art_rows * CELL_H if art else 0
    h = int(max(content_end, art_bottom) + 16)

    # ── Window chrome ──
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="GitHub stats card for @{esc(username)}">',
        f'<rect width="{W}" height="{h}" rx="10" fill="{BASE}"/>',
        f'<path d="M0,10 A10,10 0 0 1 10,0 H{W - 10} A10,10 0 0 1 {W},10 V{TITLE_H} H0 Z" fill="{MANTLE}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{CRUST}" stroke-width="1"/>',
        f'<circle cx="16" cy="15" r="5" fill="{RED}"/>',
        f'<circle cx="34" cy="15" r="5" fill="{YELLOW}"/>',
        f'<circle cx="52" cy="15" r="5" fill="{GREEN}"/>',
        _text(W // 2, 19, f"{username} — fastfetch", SUBTEXT1, 11, weight="600", anchor="middle"),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="none" stroke="{CRUST}" stroke-width="1"/>',
    ]

    art_parts = _art_text(art, art_x, art_y) if art else []

    return "\n".join(head + art_parts + parts + ["</svg>"])
