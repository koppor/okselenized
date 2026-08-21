"""Generate the OkSelenized dark palette.

Selenized dark re-derived in OKLCH: Selenized's hues, lightness ladder and
bright-accent tier, with all accents pinned to one uniform Oklab lightness
(the OkSolar idea) and chroma clamped to the sRGB gamut.

Outputs okselenized-dark.json and preview.html next to this script.
"""
import json
import math
import os

# ---- knobs -----------------------------------------------------------------
ACCENT_L = 67.0   # ponytail: uniform accent lightness; raise for airier accents
                  # at the cost of red/magenta chroma (gamut shrinks with L)
BR_DELTA = 4.5    # bright tier = ACCENT_L + BR_DELTA (Selenized's measured gap)
MONO_HUE = 220.0  # hue of all monotones (Selenized's teal-blue background)

# Selenized dark, measured in OKLCH: (L, C, H). Hues/chromas are kept,
# accent L is replaced by ACCENT_L, monotone hue snapped to MONO_HUE.
MONOTONES = {  # name: (L, C)
    "bg_0":  (33.2, 0.040),
    "bg_1":  (37.6, 0.040),
    "bg_2":  (44.7, 0.037),
    "dim_0": (62.5, 0.020),
    "fg_0":  (79.2, 0.012),
    "fg_1":  (87.5, 0.010),
}
ACCENT_HUES = {  # name: (C, H) from Selenized dark
    "red":     (0.187, 26.4),
    "orange":  (0.135, 49.4),
    "yellow":  (0.135, 90.9),
    "green":   (0.145, 133.3),
    "cyan":    (0.110, 185.1),
    "blue":    (0.150, 255.3),
    "violet":  (0.135, 300.9),
    "magenta": (0.155, 346.2),
}

# ---- OKLCH -> sRGB ----------------------------------------------------------
def oklch_to_rgb(L, C, H):
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def enc(c):
        c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return c
    return tuple(enc(c) for c in (r, g, bb))

def in_gamut(rgb, eps=1e-4):
    return all(-eps <= c <= 1 + eps for c in rgb)

def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(round(min(1, max(0, c)) * 255) for c in rgb)

def clamp_chroma(L, C, H):
    """Largest chroma <= C that stays inside sRGB at this L and H."""
    if in_gamut(oklch_to_rgb(L / 100, C, H)):
        return C
    lo, hi = 0.0, C
    for _ in range(40):
        mid = (lo + hi) / 2
        if in_gamut(oklch_to_rgb(L / 100, mid, H)):
            lo = mid
        else:
            hi = mid
    return lo

def make(L, C, H):
    C = clamp_chroma(L, C, H)
    return {"hex": to_hex(oklch_to_rgb(L / 100, C, H)),
            "oklch": [round(L, 1), round(C, 3), round(H, 1)]}

# ---- build ------------------------------------------------------------------
palette = {}
for name, (L, C) in MONOTONES.items():
    palette[name] = make(L, C, MONO_HUE)
for name, (C, H) in ACCENT_HUES.items():
    palette[name] = make(ACCENT_L, C, H)
    palette["br_" + name] = make(ACCENT_L + BR_DELTA, C, H)

# Conventional ANSI mapping (Selenized's scheme: no gray in a bright slot).
ANSI = ["bg_1", "red", "green", "yellow", "blue", "magenta", "cyan", "dim_0",
        "bg_2", "br_red", "br_green", "br_yellow", "br_blue", "br_magenta",
        "br_cyan", "fg_1"]

# ---- checks -----------------------------------------------------------------
def wcag(fg_hex, bg_hex):
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                   for c in (r, g, b))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1, l2 = sorted((lum(fg_hex), lum(bg_hex)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

bg = palette["bg_0"]["hex"]
assert wcag(palette["fg_0"]["hex"], bg) >= 6.0, "main text below Selenized's 6.07"
assert wcag(palette["dim_0"]["hex"], bg) >= 3.2, "comments below Selenized's 3.23"
for n in ACCENT_HUES:
    assert palette[n]["oklch"][0] == ACCENT_L, "accent L not uniform"
    assert wcag(palette[n]["hex"], bg) >= 3.5, f"{n} accent contrast too low"
    assert palette["br_" + n]["oklch"][0] > palette[n]["oklch"][0]
assert len(set(ANSI)) == 16 and all(n in palette for n in ANSI)

# ---- output -----------------------------------------------------------------
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "okselenized-dark.json"), "w") as f:
    json.dump({"name": "OkSelenized dark", "palette": palette, "ansi": ANSI},
              f, indent=2)

print(f"{'name':12} {'hex':>8}   {'L':>5} {'C':>6} {'H':>6}   {'WCAG on bg_0':>12}")
for name, v in palette.items():
    L, C, H = v["oklch"]
    print(f"{name:12} {v['hex']:>8}   {L:5.1f} {C:6.3f} {H:6.1f}   {wcag(v['hex'], bg):12.2f}")

# minimal visual preview
sw = "".join(
    f'<div><span style="background:{v["hex"]}"></span>{n}<code>{v["hex"]}</code></div>'
    for n, v in palette.items())
term = f"""<pre style="background:{bg};color:{palette['fg_0']['hex']};padding:1em">
<span style="color:{palette['dim_0']['hex']}"># comment: ls output below uses normal + bright ANSI slots</span>
<span style="color:{palette['blue']['hex']}">drwxr-xr-x</span>  <span style="color:{palette['br_blue']['hex']}">bin/</span>   <span style="color:{palette['green']['hex']}">OK</span> <span style="color:{palette['br_green']['hex']}">OK-bright</span>
<span style="color:{palette['red']['hex']}">error:</span> <span style="color:{palette['br_red']['hex']}">bright error</span>  <span style="color:{palette['yellow']['hex']}">warn</span> <span style="color:{palette['br_yellow']['hex']}">bright warn</span>
<span style="color:{palette['magenta']['hex']}">magenta</span> <span style="color:{palette['violet']['hex']}">violet</span> <span style="color:{palette['cyan']['hex']}">cyan</span> <span style="color:{palette['orange']['hex']}">orange</span>
<span style="color:{palette['fg_1']['hex']};font-weight:bold">emphasized text</span> on bg_0
</pre>"""
with open(os.path.join(here, "preview.html"), "w") as f:
    f.write(f"""<title>OkSelenized dark</title>
<style>body{{font-family:monospace;background:#1a1a1a;color:#ccc;margin:2em}}
div span{{display:inline-block;width:3em;height:1.4em;vertical-align:middle;margin-right:.6em}}
code{{margin-left:.6em;color:#888}}</style>
<h2>OkSelenized dark</h2>{term}{sw}""")
print("\nwrote okselenized-dark.json, preview.html")
