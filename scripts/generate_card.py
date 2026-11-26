#!/usr/bin/env python3
"""Generate the Catppuccin Macchiato info card (main entry point).

Pipeline: fetch GitHub data → avatar to ASCII art → render SVG.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from avatar_ascii import fetch_ascii_art
from fetch_data import fetch
from render_svg import render


def main():
    username = os.environ.get("GITHUB_USERNAME", "Abyss-PlayerEG")
    output_dir = os.environ.get("OUTPUT_DIR", "img")

    print(f"📊 Generating info card for @{username}...")

    data = fetch(username)

    art = None
    try:
        art = fetch_ascii_art(data["profile"]["avatar_url"])
    except Exception as e:
        print(f"  ⚠️  Avatar art failed ({e}), rendering without art", file=sys.stderr)

    svg = render(username, data, art)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "stats.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  ✅ {output_path}")
    print("🎉 Done!")


if __name__ == "__main__":
    main()
