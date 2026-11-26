#!/usr/bin/env python3
"""Generate GitHub stats SVG cards: language distribution + join date."""

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

# ── Color palette (GitHub-like) ──────────────────────────────────────────────
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
    "Rust": "#dea584",
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
    """GET request to GitHub API with rate-limit handling."""
    resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=30)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        print("⚠️  Rate limited, waiting 60s...", file=sys.stderr)
        import time
        time.sleep(60)
        resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_all_repos() -> list[dict]:
    """Fetch all repos (public + private) for the user, paginated."""
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
    """Aggregate language bytes across all repos."""
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
    """Fetch account creation date."""
    user = api_get(f"/users/{USERNAME}")
    created = user["created_at"]  # ISO format: 2020-01-01T00:00:00Z
    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d")


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def generate_language_svg(lang_bytes: dict[str, int]) -> str:
    """Generate dark-themed horizontal bar chart for language distribution."""
    total = sum(lang_bytes.values())
    if total == 0:
        return _empty_card("No language data")

    # Sort and take top 8
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:8]
    top_total = sum(v for _, v in sorted_langs)

    # SVG dimensions
    width = 480
    row_height = 36
    header_height = 60
    padding = 24
    height = header_height + len(sorted_langs) * row_height + padding

    # Bar area
    bar_x = 130
    bar_max_width = width - bar_x - 80

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Background
    parts.append(f'<rect width="{width}" height="{height}" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')

    # Title
    parts.append(f'<text x="{padding}" y="32" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="#e6edf3">🌐 Language Distribution</text>')
    parts.append(f'<text x="{width - padding}" y="32" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#8b949e">{format_bytes(total)} total</text>')

    # Divider
    parts.append(f'<line x1="{padding}" y1="{header_height - 8}" x2="{width - padding}" y2="{header_height - 8}" stroke="#21262d" stroke-width="1"/>')

    # Language bars
    for i, (lang, size) in enumerate(sorted_langs):
        y = header_height + i * row_height
        pct = size / top_total * 100 if top_total else 0
        bar_width = max(int(bar_max_width * pct / 100), 4)
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)

        # Language name
        parts.append(f'<text x="{padding}" y="{y + 22}" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#c9d1d9">{lang}</text>')

        # Bar background
        parts.append(f'<rect x="{bar_x}" y="{y + 10}" width="{bar_max_width}" height="16" rx="4" fill="#161b22"/>')

        # Bar fill
        parts.append(f'<rect x="{bar_x}" y="{y + 10}" width="{bar_width}" height="16" rx="4" fill="{color}"/>')

        # Percentage
        parts.append(f'<text x="{width - padding}" y="{y + 22}" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#8b949e">{pct:.1f}%</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def generate_join_svg(join_date: str) -> str:
    """Generate dark-themed card showing GitHub join date."""
    dt = datetime.fromisoformat(join_date).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    years = (now - dt).days // 365
    months = ((now - dt).days % 365) // 30

    if years > 0:
        tenure = f"{years}y {months}m"
    else:
        tenure = f"{months}m"

    width = 480
    height = 140
    padding = 24

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Background
    parts.append(f'<rect width="{width}" height="{height}" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')

    # Title
    parts.append(f'<text x="{padding}" y="32" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="#e6edf3">📅 GitHub Journey</text>')

    # Divider
    parts.append(f'<line x1="{padding}" y1="48" x2="{width - padding}" y2="48" stroke="#21262d" stroke-width="1"/>')

    # Join date row
    parts.append(f'<text x="{padding}" y="78" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Joined</text>')
    parts.append(f'<text x="{padding + 70}" y="78" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600" fill="#58a6ff">{join_date}</text>')

    # Tenure row
    parts.append(f'<text x="{padding}" y="110" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Tenure</text>')
    parts.append(f'<text x="{padding + 70}" y="110" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600" fill="#3fb950">{tenure}</text>')

    # Decorative calendar icon (simple)
    icon_x = width - 70
    icon_y = 65
    parts.append(f'<rect x="{icon_x}" y="{icon_y}" width="44" height="44" rx="6" fill="#161b22" stroke="#30363d"/>')
    parts.append(f'<text x="{icon_x + 22}" y="{icon_y + 30}" text-anchor="middle" font-size="22">🗓️</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def _empty_card(msg: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="100" viewBox="0 0 480 100">
<rect width="480" height="100" rx="8" fill="#0d1117" stroke="#30363d"/>
<text x="240" y="55" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="#8b949e">{msg}</text>
</svg>'''


def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN is required (needs repo scope for private repos)", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"📊 Generating stats for {USERNAME}...")

    # 1. Language distribution
    print("  → Fetching repos...")
    repos = get_all_repos()
    print(f"  → Found {len(repos)} repos")

    print("  → Aggregating languages...")
    lang_bytes = get_language_stats(repos)
    lang_svg = generate_language_svg(lang_bytes)

    lang_path = os.path.join(OUTPUT_DIR, "langs.svg")
    with open(lang_path, "w", encoding="utf-8") as f:
        f.write(lang_svg)
    print(f"  ✅ {lang_path}")

    # 2. Join date
    print("  → Fetching join date...")
    join_date = get_join_date()
    join_svg = generate_join_svg(join_date)

    join_path = os.path.join(OUTPUT_DIR, "journey.svg")
    with open(join_path, "w", encoding="utf-8") as f:
        f.write(join_svg)
    print(f"  ✅ {join_path}")

    print("🎉 Done!")


if __name__ == "__main__":
    main()
