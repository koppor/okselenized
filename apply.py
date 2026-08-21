#!/usr/bin/env python3
"""Apply okselenized-dark.json to the current terminal via OSC escapes.
Run: python3 apply.py   (reset by opening a new terminal tab)"""
import json, sys

d = json.load(open("okselenized-dark.json"))
p = d["palette"]
out = []
for i, name in enumerate(d["ansi"]):
    out.append(f"\033]4;{i};{p[name]['hex']}\033\\")
out.append(f"\033]10;{p['fg_0']['hex']}\033\\")   # foreground
out.append(f"\033]11;{p['bg_0']['hex']}\033\\")   # background
out.append(f"\033]12;{p['fg_1']['hex']}\033\\")   # cursor
sys.stdout.write("".join(out))
print(f"applied {d['name']}")
