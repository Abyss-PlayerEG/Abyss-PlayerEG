#!/usr/bin/env python3
"""Download a GitHub avatar and convert it to a colored ASCII grid."""

import io
import sys

import requests
from PIL import Image

RAMP = " .:-=+*#%@"  # dark → light


def _lum(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def fetch_ascii_art(avatar_url: str, cols: int = 49, rows: int = 28) -> list[list[tuple[str, str]]]:
    """Return a rows×cols grid of (char, '#rrggbb'), spaces skipped as (' ', '')."""
    url = avatar_url.split("?")[0] + "?s=512"
    print(f"  → Downloading avatar...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    img = img.resize((cols, rows), Image.LANCZOS)

    pixels = list(img.getdata())
    mean = sum(_lum(*p) for p in pixels) / len(pixels)

    # Dark avatars: flip the ramp and brighten colors so art stays visible
    # on the dark card background.
    ramp = RAMP[::-1] if mean < 100 else RAMP
    factor = min(1.7, 110 / max(mean, 1)) if mean < 110 else 1.0

    grid: list[list[tuple[str, str]]] = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b = pixels[y * cols + x]
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            lum = _lum(r, g, b)
            idx = int(lum / 255 * (len(ramp) - 1))
            row.append((ramp[idx], f"#{r:02x}{g:02x}{b:02x}"))
        grid.append(row)
    return grid
