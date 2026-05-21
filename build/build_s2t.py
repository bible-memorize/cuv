#!/usr/bin/env python3
"""
Generate s2t.js — a Simplified→Traditional character map.

Source: OpenCC project's STCharacters.txt + TWVariants.txt
Output: app/memorize-cuv/s2t.js  (window.S2T = { "简": "簡", ... })

When OpenCC lists multiple Traditional candidates for one Simplified character,
pick the first (most common) — this is a coarse one-to-one mapping suitable
for fuzzy comparison, not authoritative typography.
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "app/memorize-cuv/s2t.js"

ST_URL = "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/STCharacters.txt"
# General Traditional ↔ TW-variant Traditional. We read this REVERSED so any
# TW-variant char in the recognizer output (e.g. 著, 裡, 爲) gets normalized to
# the general-Traditional form used by CUV (着, 裏, 為).
TW_URL = "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TWVariants.txt"


def fetch(url: str) -> str:
    print(f"GET {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_first_target(text: str) -> dict:
    """Parse OpenCC dict format: 'src\\ttgt1 tgt2 ...' → {src: tgt1}."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        src = parts[0]
        tgts = parts[1].split()
        if not tgts or src == tgts[0]:
            continue
        out[src] = tgts[0]
    return out


def parse_reverse(text: str) -> dict:
    """Reverse OpenCC dict: 'general\\ttw1 tw2 ...' → {tw1: general, tw2: general, ...}."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        general = parts[0]
        for tw in parts[1].split():
            if tw != general and tw not in out:
                out[tw] = general
    return out


def main():
    s2t = parse_first_target(fetch(ST_URL))
    print(f"  STCharacters: {len(s2t):,}", flush=True)
    tw2t = parse_reverse(fetch(TW_URL))
    print(f"  TWVariants (reversed): {len(tw2t):,}", flush=True)

    # Merge. Apply STCharacters first; then for any value still containing TW
    # variant chars, map back to general. Build a single one-shot map.
    merged = dict(s2t)
    # Compose: chain through tw2t. If a Simplified char maps to a TW-variant char,
    # we want the final value to be the general Traditional. Apply tw2t to the
    # output of s2t.
    for k, v in list(merged.items()):
        if v in tw2t:
            merged[k] = tw2t[v]
    # Also include direct tw2t entries (handle case where recognizer returns TW
    # variants directly without going through Simplified).
    for k, v in tw2t.items():
        merged.setdefault(k, v)
    print(f"  merged map: {len(merged):,}", flush=True)
    s2t = merged

    # Emit as a compact JS file
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Use JSON for compactness and safe escaping
    json_blob = json.dumps(s2t, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(
        "// Auto-generated. Source: OpenCC STCharacters.txt. Do not edit.\n"
        f"window.S2T = {json_blob};\n",
        encoding="utf-8",
    )
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(ROOT)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
