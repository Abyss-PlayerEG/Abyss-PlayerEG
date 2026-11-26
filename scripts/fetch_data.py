#!/usr/bin/env python3
"""Fetch GitHub profile, repository and language stats."""

import os
import sys
import time

import requests

API_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def api_get(path: str) -> dict | list:
    resp = requests.get(f"{API_BASE}{path}", headers=_headers(), timeout=30)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        print("⚠️  Rate limited, waiting 60s...", file=sys.stderr)
        time.sleep(60)
        resp = requests.get(f"{API_BASE}{path}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch(username: str) -> dict:
    """Fetch profile + aggregated repo/language stats for a user."""
    print(f"  → Fetching profile @{username}...")
    profile = api_get(f"/users/{username}")

    print("  → Fetching repos...")
    repos = []
    page = 1
    while True:
        data = api_get(f"/users/{username}/repos?per_page=100&page={page}&type=all")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    print("  → Aggregating languages...")
    lang_bytes: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            langs = api_get(f"/repos/{username}/{repo['name']}/languages")
            for lang, size in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + size
        except requests.RequestException as e:
            print(f"  ⚠️  Skip {repo['name']}: {e}", file=sys.stderr)

    return {
        "profile": profile,
        "total_stars": total_stars,
        "language_bytes": lang_bytes,
    }
