#!/usr/bin/env python3
"""Render the Catppuccin Macchiato neofetch-style info card as SVG."""

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

LANG_COLORS = {
    "Python": BLUE, "Java": PEACH, "JavaScript": YELLOW, "TypeScript": SAPPHIRE,
    "Vue": GREEN, "HTML": RED, "CSS": MAUVE, "Go": TEAL, "Shell": GREEN,
    "Rust": PEACH, "C": SUBTEXT1, "C++": MAROON, "C#": MAUVE, "Ruby": RED,
    "PHP": LAVENDER, "Dart": SAPPHIRE, "SCSS": PINK, "Lua": BLUE,
    "Kotlin": PEACH, "Swift": PEACH,
}
DEFAULT_LANG_COLOR = LAVENDER

# ── Nerd Font icons (rendered as embedded paths — no font needed) ────────────
from .icons import ICONS, UPM  # noqa: E402
from .heatmap import DAYS, build_matrix, classify  # noqa: E402
from .font import FONT_B64, FONT_FORMAT  # noqa: E402

# Embedded subset font: SVG-as-image cannot load external fonts, so the
# @font-face must ride inside the file as a data URI.
FONT_FACE = (
    "<style>"
    "@font-face{"
    "font-family:'JetBrainsMono Nerd Font';"
    f"src:url(data:font/{FONT_FORMAT};base64,{FONT_B64}) format('{FONT_FORMAT}');"
    "font-weight:400;font-style:normal;"
    "}"
    "</style>"
)

IC_USER = "user"
IC_PENCIL = "pencil"
IC_MAP = "map"
IC_BRIEFCASE = "briefcase"
IC_CALENDAR = "calendar"
IC_LINK = "link"
IC_FOLDER = "folder"
IC_STAR = "star"
IC_USERS = "users"
IC_CODE = "code"
IC_TH = "th"

FONT = "'JetBrainsMono Nerd Font', Menlo, Monaco, monospace"
MONO = FONT

# ── Layout ───────────────────────────────────────────────────────────────────
W = 860
TITLE_H = 30
PAD = 18
CELL_W = 6.0
CELL_H = 10.5
ART_FONT = 10
ART_COLS = 58
ART_ROWS = 33
ROW_H = 20
BAR_H = 19
LINE_ADV = 20  # row pitch after a separator line


def esc(s: str) -> str:
    return escape(str(s))


def _text(x, y, s, fill, size=12, weight=None, anchor=None, mono=True):
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"', f'font-size="{size}"']
    if mono:
        attrs.append(f'font-family="{MONO}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    return f'<text {" ".join(attrs)}>{s}</text>'


def _line(x1, y, x2, color=SURFACE1):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1"/>'


def _icon(x, y, name, size, color):
    """Draw an icon glyph outline as a vector path at the given baseline."""
    s = size / UPM
    d = ICONS[name]
    return (
        f'<path d="{d}" fill="{color}" '
        f'transform="translate({x},{y}) scale({s:.4f},{-s:.4f})"/>'
    )


def _truncate(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _field(y, right_x, icon, label, value, color):
    """Icon + 'Label:' + value row."""
    parts = [
        _icon(right_x, y, icon, 12, color),
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
    tenure_long = f"{years} years, {months} months" if years > 0 else f"{months} months"
    joined = created.strftime("%Y-%m-%d")

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:8]
    top_total = sum(v for _, v in sorted_langs) or 1

    # ── Geometry ──
    art_cols = len(art[0]) if art else 0
    art_rows = len(art) if art else 0
    art_w = art_cols * CELL_W
    art_x = PAD
    art_y = TITLE_H + 14
    right_x = PAD + (art_w + 70 if art else 0)
    right_w = W - right_x - PAD

    parts = []

    # ── Top-right timestamp block ──
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    parts.append(_text(W - PAD, TITLE_H + 14, "UTC · LAST UPDATED", OVERLAY0, 10, anchor="end"))
    parts.append(_text(W - PAD, TITLE_H + 32, stamp, SKY, 14, weight="700", anchor="end"))

    # ── Big title ──
    y = TITLE_H + 26
    parts.append(_text(right_x, y, f"{esc(username)}@github", GREEN, 16, weight="700"))
    y = TITLE_H + 50
    parts.append(_line(right_x, y, W - PAD))
    y += LINE_ADV

    # ── Group 1: profile fields ──
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
        y, row_parts = _field(y, right_x, icon, label, _truncate(value, 38), color)
        parts += row_parts

    # ── Group 2: GitHub stats ──
    parts.append(_line(right_x, y, W - PAD))
    y += LINE_ADV
    stats = [
        (IC_FOLDER, "Repos", str(profile["public_repos"]), BLUE),
        (IC_STAR, "Stars", str(total_stars), YELLOW),
        (IC_USER, "Followers", str(profile["followers"]), GREEN),
        (IC_USERS, "Following", str(profile["following"]), MAUVE),
    ]
    for icon, label, value, color in stats:
        y, row_parts = _field(y, right_x, icon, label, value, color)
        parts += row_parts

    # ── Languages section ──
    parts.append(_line(right_x, y, W - PAD))
    y += LINE_ADV
    parts.append(_icon(right_x, y, IC_CODE, 12, SUBTEXT0))
    parts.append(_text(right_x + 22, y, "Languages · Public Repositories", SUBTEXT0, 12))

    # Block-character bars
    name_w = 95
    pct_w = 45
    pitch = 9  # block width 7 + gap 2
    n_blocks = max(10, int((right_w - name_w - pct_w) / pitch))
    bar_x = right_x + name_w
    for lang, size in sorted_langs:
        y += BAR_H
        pct = size / top_total * 100
        color = LANG_COLORS.get(lang, DEFAULT_LANG_COLOR)
        parts.append(_text(right_x, y, esc(lang), color, 11))
        filled = max(1, round(pct / 100 * n_blocks))
        for b in range(n_blocks):
            bx = bar_x + b * pitch
            fill = color if b < filled else SURFACE0
            parts.append(f'<rect x="{bx}" y="{y - 9}" width="7" height="11" rx="1" fill="{fill}"/>')
        parts.append(_text(W - PAD, y, f"{pct:.1f}%", SUBTEXT1, 11, anchor="end"))
    y += 16
    content_end = y + 14

    # ── Left column bottom: separator + whoami/age prompt block ──
    art_bottom = art_y + art_rows * CELL_H if art else 0
    left_line_y = art_bottom + 10
    prompt_x = PAD
    prompt_y = left_line_y + 18
    prompt_lines = [
        [(f'<tspan fill="{GREEN}" font-weight="700">{esc(username)}</tspan>'
          f'<tspan fill="{SUBTEXT0}">@github</tspan>'
          f'<tspan fill="{BLUE}">:~$</tspan>'
          f'<tspan fill="{TEXT}"> whoami</tspan>')],
        [esc(username)],
        [(f'<tspan fill="{GREEN}" font-weight="700">{esc(username)}</tspan>'
          f'<tspan fill="{SUBTEXT0}">@github</tspan>'
          f'<tspan fill="{BLUE}">:~$</tspan>'
          f'<tspan fill="{TEXT}"> age</tspan>')],
        [esc(tenure_long)],
    ]
    left_parts = [_line(PAD, left_line_y, PAD + art_w + 34)]
    for i, line in enumerate(prompt_lines):
        left_parts.append(_text(prompt_x, prompt_y + i * 16, "".join(line), TEXT, 12))
    left_bottom = prompt_y + (len(prompt_lines) - 1) * 16

    # ── Commit heatmap band (full width, bottom) ──
    matrix = build_matrix(data.get("commit_times", []))
    levels = classify(matrix)
    total_commits = sum(sum(row) for row in matrix)

    band = []
    base = max(content_end, left_bottom) + 8
    band.append(_line(PAD, base, W - PAD))
    header_y = base + 22
    band.append(_icon(PAD, header_y, IC_TH, 12, SUBTEXT0))
    band.append(_text(PAD + 22, header_y, "Commit Heatmap · Last 12 Months", SUBTEXT0, 12))
    band.append(_text(W - PAD, header_y, f"{total_commits} commits", GREEN, 12, weight="700", anchor="end"))

    grid_x = PAD + 34
    grid_w = W - PAD - grid_x
    pitch = grid_w / 24
    cell_w = pitch - 6

    hour_y = header_y + 18
    for hcol in range(0, 24, 4):
        cx = grid_x + hcol * pitch + cell_w / 2
        band.append(_text(cx, hour_y, f"{hcol:02d}", OVERLAY0, 9, anchor="middle"))

    heat_opacity = [0, 0.3, 0.55, 0.8, 1.0]
    row0_y = hour_y + 24
    for d in range(7):
        ry = row0_y + d * 16
        band.append(_text(PAD, ry, DAYS[d], SUBTEXT0, 10))
        for hcol in range(24):
            lv = levels[d][hcol]
            x = grid_x + hcol * pitch
            if lv == 0:
                band.append(f'<rect x="{x:.1f}" y="{ry - 11}" width="{cell_w:.1f}" height="12" rx="2" fill="{SURFACE0}"/>')
            else:
                band.append(
                    f'<rect x="{x:.1f}" y="{ry - 11}" width="{cell_w:.1f}" height="12" rx="2" '
                    f'fill="{GREEN}" fill-opacity="{heat_opacity[lv]}"/>'
                )
    band_end = row0_y + 6 * 16 + 14

    # ── Window height ──
    h = int(band_end + 14)

    # ── Window chrome ──
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="GitHub stats card for @{esc(username)}">',
        FONT_FACE,
        f'<rect width="{W}" height="{h}" rx="10" fill="{BASE}"/>',
        f'<path d="M0,10 A10,10 0 0 1 10,0 H{W - 10} A10,10 0 0 1 {W},10 V{TITLE_H} H0 Z" fill="{MANTLE}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{CRUST}" stroke-width="1"/>',
        f'<circle cx="16" cy="15" r="5" fill="{RED}"/>',
        f'<circle cx="34" cy="15" r="5" fill="{YELLOW}"/>',
        f'<circle cx="52" cy="15" r="5" fill="{GREEN}"/>',
        _text(W // 2, 19, f"{username} — neofetch", SUBTEXT1, 11, weight="600", anchor="middle"),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="none" stroke="{CRUST}" stroke-width="1"/>',
    ]

    art_parts = _art_text(art, art_x, art_y) if art else []

    return "\n".join(head + art_parts + left_parts + parts + band + ["</svg>"])
