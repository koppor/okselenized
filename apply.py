#!/usr/bin/env python3
"""Apply an OkSelenized palette to the current terminal via OSC escapes.
Run: python3 apply.py [dark|black|light]   (reset by opening a new tab)"""
import json, sys
from pathlib import Path

variant = sys.argv[1] if len(sys.argv) > 1 else "dark"
d = json.loads((Path(__file__).resolve().parent / f"okselenized-{variant}.json").read_text())
p = d["palette"]
out = []
for i, name in enumerate(d["ansi"]):
    out.append(f"\033]4;{i};{p[name]['hex']}\033\\")
out.append(f"\033]10;{p['fg_0']['hex']}\033\\")   # foreground
out.append(f"\033]11;{p['bg_0']['hex']}\033\\")   # background
out.append(f"\033]12;{p['fg_1']['hex']}\033\\")   # cursor
sys.stdout.write("".join(out))
print(f"applied {d['name']}")
