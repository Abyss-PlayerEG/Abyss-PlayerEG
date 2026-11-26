#!/usr/bin/env python3
"""Generate a single GitHub stats SVG card: language tag cloud + join date."""

import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = os.environ.get("GITHUB_USERNAME", "Abyss-PlayerEG")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "img")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

API_BASE = "https://api.github.com"

LANG_COLORS = {
    "Python": "#3572A5",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Go": "#00ADD8",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "Vue": "#41b883",
    "SCSS": "#c6538c",
    "PowerShell": "#012456",
    "Batchfile": "#C1F12E",
    "Makefile": "#427819",
    "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B",
    "CMake": "#DA3434",
}

DEFAULT_COLOR = "#8b949e"


def api_get(path: str) -> dict | list:
    resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=30)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        print("⚠️  Rate limited, waiting 60s...", file=sys.stderr)
        import time
        time.sleep(60)
        resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_all_repos() -> list[dict]:
    repos = []
    page = 1
    while True:
        data = api_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=all")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_language_stats(repos: list[dict]) -> dict[str, int]:
    lang_bytes: dict[str, int] = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            langs = api_get(f"/repos/{USERNAME}/{repo['name']}/languages")
            for lang, size in langs.items():
                lang_bytes[lang] += size
        except requests.RequestException as e:
            print(f"  ⚠️  Skip {repo['name']}: {e}", file=sys.stderr)
    return dict(lang_bytes)


def get_join_date() -> str:
    user = api_get(f"/users/{USERNAME}")
    created = user["created_at"]
    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d")


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def generate_card(lang_bytes: dict[str, int], join_date: str) -> str:
    """Generate a single dark-space-black card with tag cloud + join date."""
    total = sum(lang_bytes.values())
    now = datetime.now(timezone.utc)
    update_time = now.strftime("%Y-%m-%d %H:%M UTC")

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:12]
    top_total = sum(v for _, v in sorted_langs)

    # ── Dimensions ──
    width = 520
    padding = 28
    header_height = 72
    cloud_height = 220
    divider_gap = 24
    info_height = 100
    footer_height = 36
    height = header_height + cloud_height + divider_gap + info_height + footer_height

    # ── Tag cloud layout ──
    max_pct = sorted_langs[0][1] / top_total * 100 if sorted_langs and top_total else 1
    tags = []
    for lang, size in sorted_langs:
        pct = size / top_total * 100 if top_total else 0
        norm = pct / max_pct if max_pct else 0
        font_size = int(14 + norm * 28)
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        tags.append((lang, pct, font_size, color))

    cloud_parts = []
    current_x = padding
    current_y = header_height + 40
    line_height = 52
    max_x = width - padding

    for lang, pct, font_size, color in tags:
        text_width = len(lang) * font_size * 0.6 + 40
        if current_x + text_width > max_x:
            current_x = padding
            current_y += line_height

        cloud_parts.append(f'''<g class="lang-tag" style="cursor:default">
  <title>{lang}: {pct:.1f}%</title>
  <text x="{current_x}" y="{current_y}" font-family="Segoe UI, Arial, sans-serif" font-size="{font_size}" font-weight="{'700' if font_size > 30 else '600'}" fill="{color}" opacity="{0.6 + norm * 0.4:.2f}">{lang}</text>
  <text x="{current_x + len(lang) * font_size * 0.6 + 6}" y="{current_y}" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#484f58">{pct:.1f}%</text>
</g>''')
        current_x += text_width

    cloud_svg = "\n".join(cloud_parts)

    # ── Join date info ──
    dt = datetime.fromisoformat(join_date).replace(tzinfo=timezone.utc)
    years = (now - dt).days // 365
    months = ((now - dt).days % 365) // 30
    tenure = f"{years}y {months}m" if years > 0 else f"{months}m"

    info_y = header_height + cloud_height + divider_gap

    # ── Build SVG ──
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    parts.append('''<style>
  .lang-tag text:first-child { transition: opacity 0.2s; }
  .lang-tag:hover text:first-child { opacity: 1 !important; }
  .lang-tag:hover text:last-child { fill: #c9d1d9; }
  .card-border { transition: stroke 0.3s; }
  svg:hover .card-border { stroke: #30363d; }
</style>''')

    # Background — deep space black
    parts.append(f'<rect width="{width}" height="{height}" rx="12" fill="#010409" stroke="#21262d" stroke-width="1" class="card-border"/>')

    # Gradient top accent bar
    parts.append(f'''<defs>
  <linearGradient id="topAccent" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#1f6feb;stop-opacity:1" />
    <stop offset="50%" style="stop-color:#a371f7;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#3fb950;stop-opacity:1" />
  </linearGradient>
</defs>
<rect x="12" y="0" width="{width - 24}" height="3" rx="1.5" fill="url(#topAccent)"/>''')

    # ── Header ──
    parts.append(f'<text x="{padding}" y="44" font-size="22">📊</text>')
    parts.append(f'<text x="{padding + 32}" y="44" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="#e6edf3">GitHub Stats</text>')
    parts.append(f'<text x="{width - padding}" y="44" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#484f58">@{USERNAME}</text>')

    parts.append(f'<text x="{padding}" y="64" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#8b949e">🌐 {format_bytes(total)} across {len(sorted_langs)} languages</text>')

    parts.append(f'<line x1="{padding}" y1="{header_height - 4}" x2="{width - padding}" y2="{header_height - 4}" stroke="#21262d" stroke-width="1"/>')

    # ── Tag Cloud ──
    parts.append(cloud_svg)

    # ── Divider before info ──
    parts.append(f'<line x1="{padding}" y1="{info_y}" x2="{width - padding}" y2="{info_y}" stroke="#21262d" stroke-width="1"/>')

    # ── Join Date Info ──
    info_content_y = info_y + 32

    parts.append(f'<text x="{padding}" y="{info_content_y}" font-size="18">📅</text>')
    parts.append(f'<text x="{padding + 26}" y="{info_content_y}" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Joined</text>')
    parts.append(f'<text x="{padding + 90}" y="{info_content_y}" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600" fill="#58a6ff">{join_date}</text>')

    parts.append(f'<text x="{width - padding - 160}" y="{info_content_y}" font-size="18">⏱️</text>')
    parts.append(f'<text x="{width - padding - 134}" y="{info_content_y}" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Tenure</text>')
    parts.append(f'<text x="{width - padding - 70}" y="{info_content_y}" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600" fill="#3fb950">{tenure}</text>')

    # ── Footer: Update timestamp ──
    footer_y = height - 14
    parts.append(f'<line x1="{padding}" y1="{height - footer_height + 4}" x2="{width - padding}" y2="{height - footer_height + 4}" stroke="#21262d" stroke-width="1"/>')
    parts.append(f'<text x="{padding}" y="{footer_y}" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="#484f58">🕐 Updated {update_time}</text>')
    parts.append(f'<text x="{width - padding}" y="{footer_y}" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="#484f58">via GitHub Actions</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN is required", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"📊 Generating stats card for {USERNAME}...")

    print("  → Fetching repos...")
    repos = get_all_repos()
    print(f"  → Found {len(repos)} repos")

    print("  → Aggregating languages...")
    lang_bytes = get_language_stats(repos)

    print("  → Fetching join date...")
    join_date = get_join_date()

    print("  → Generating SVG...")
    svg = generate_card(lang_bytes, join_date)

    output_path = os.path.join(OUTPUT_DIR, "stats.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  ✅ {output_path}")

    print("🎉 Done!")


if __name__ == "__main__":
    main()
