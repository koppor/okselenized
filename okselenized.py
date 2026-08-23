"""Generate the OkSelenized palettes (dark, black, light).

Selenized re-derived in OKLCH: Selenized's hues, lightness ladders and
bright-accent tiers, with all accents pinned to one uniform Oklab lightness
per variant (the OkSolar idea) and chroma clamped to the sRGB gamut.

Outputs okselenized-<variant>.json / .minttyrc and preview.html.
"""
import json
import math
import os

# Accent hues and base chroma, shared by all variants (from Selenized dark).
ACCENT_HUES = {  # name: (C, H)
    "red":     (0.187, 26.4),
    "orange":  (0.135, 49.4),
    "yellow":  (0.135, 90.9),
    "green":   (0.145, 133.3),
    "cyan":    (0.110, 185.1),
    "blue":    (0.150, 255.3),
    "violet":  (0.135, 300.9),
    "magenta": (0.155, 346.2),
}

# Per-variant design tables, anchored on the corresponding Selenized variant
# measured in OKLCH. monotones: name -> (L, C, H). accent_l is the uniform
# Oklab accent lightness (ponytail: the calibration knob — raising it gives
# airier accents but shrinks sRGB gamut for red/magenta). br_delta is the
# bright tier's lightness offset (negative on light: brighter == darker
# there). floors are WCAG minimums, chosen to match or beat Selenized.
VARIANTS = {
    "dark": dict(
        monotones={"bg_0": (33.2, 0.040, 220), "bg_1": (37.6, 0.040, 220),
                   "bg_2": (44.7, 0.037, 220), "dim_0": (62.5, 0.020, 220),
                   "fg_0": (79.2, 0.012, 220), "fg_1": (87.5, 0.010, 220)},
        accent_l=67.0, br_delta=4.5, chroma_scale=1.0,
        floors=dict(fg=6.0, dim=3.2, accent=3.5),
    ),
    "black": dict(  # neutral near-black monotones, accents slightly darker
        monotones={"bg_0": (21.0, 0.0, 220), "bg_1": (26.5, 0.0, 220),
                   "bg_2": (35.0, 0.0, 220), "dim_0": (57.0, 0.0, 220),
                   "fg_0": (78.5, 0.0, 220), "fg_1": (90.0, 0.0, 220)},
        accent_l=65.0, br_delta=4.5, chroma_scale=1.0,
        floors=dict(fg=8.5, dim=3.9, accent=4.0),
    ),
    "light": dict(  # cream backgrounds, teal foregrounds, accents darker
        monotones={"bg_0": (96.4, 0.033, 90), "bg_1": (91.7, 0.032, 90),
                   "bg_2": (84.9, 0.032, 90), "dim_0": (67.4, 0.012, 168),
                   "fg_0": (50.0, 0.026, 220), "fg_1": (40.7, 0.026, 220)},
        accent_l=58.0, br_delta=-2.0, chroma_scale=1.25,
        floors=dict(fg=5.3, dim=2.6, accent=3.4),
    ),
}

# Conventional ANSI mapping (Selenized's scheme: no gray in a bright slot).
ANSI = ["bg_1", "red", "green", "yellow", "blue", "magenta", "cyan", "dim_0",
        "bg_2", "br_red", "br_green", "br_yellow", "br_blue", "br_magenta",
        "br_cyan", "fg_1"]
MINTTY = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan",
          "White", "BoldBlack", "BoldRed", "BoldGreen", "BoldYellow",
          "BoldBlue", "BoldMagenta", "BoldCyan", "BoldWhite"]

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
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
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

def wcag(fg_hex, bg_hex):
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                   for c in (r, g, b))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1, l2 = sorted((lum(fg_hex), lum(bg_hex)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

# ---- build ------------------------------------------------------------------
def build(spec):
    palette = {}
    for name, (L, C, H) in spec["monotones"].items():
        palette[name] = make(L, C, H)
    for name, (C, H) in ACCENT_HUES.items():
        C *= spec["chroma_scale"]
        palette[name] = make(spec["accent_l"], C, H)
        palette["br_" + name] = make(spec["accent_l"] + spec["br_delta"], C, H)
    return palette

def check(palette, spec):
    bg, floors = palette["bg_0"]["hex"], spec["floors"]
    assert wcag(palette["fg_0"]["hex"], bg) >= floors["fg"], "main text contrast"
    assert wcag(palette["dim_0"]["hex"], bg) >= floors["dim"], "comment contrast"
    sign = 1 if spec["br_delta"] > 0 else -1
    for n in ACCENT_HUES:
        assert palette[n]["oklch"][0] == spec["accent_l"], "accent L not uniform"
        assert wcag(palette[n]["hex"], bg) >= floors["accent"], f"{n} contrast"
        d = palette["br_" + n]["oklch"][0] - palette[n]["oklch"][0]
        assert d * sign > 0, "bright tier on wrong side"
    assert len(set(ANSI)) == 16 and all(n in palette for n in ANSI)

here = os.path.dirname(os.path.abspath(__file__))
confdir = os.path.join(here, "configurations")
os.makedirs(confdir, exist_ok=True)
previews = []
palettes = {}
for variant, spec in VARIANTS.items():
    palette = palettes[variant] = build(spec)
    check(palette, spec)
    with open(os.path.join(here, f"okselenized-{variant}.json"), "w",
              newline="\n") as f:
        json.dump({"name": f"OkSelenized {variant}", "palette": palette,
                   "ansi": ANSI}, f, indent=2)
    with open(os.path.join(confdir, f"okselenized-{variant}.minttyrc"), "w",
              newline="\n") as f:
        f.write(f"# OkSelenized {variant} - append to ~/.minttyrc\n"
                f"ForegroundColour={palette['fg_0']['hex']}\n"
                f"BackgroundColour={palette['bg_0']['hex']}\n"
                f"CursorColour={palette['fg_1']['hex']}\n")
        for mname, slot in zip(MINTTY, ANSI):
            f.write(f"{mname}={palette[slot]['hex']}\n")

    bg = palette["bg_0"]["hex"]
    print(f"== {variant} ==")
    print(f"{'name':12} {'hex':>8}   {'L':>5} {'C':>6} {'H':>6}   {'WCAG on bg_0':>12}")
    for name, v in palette.items():
        L, C, H = v["oklch"]
        print(f"{name:12} {v['hex']:>8}   {L:5.1f} {C:6.3f} {H:6.1f}"
              f"   {wcag(v['hex'], bg):12.2f}")

    sw = "".join(
        f'<div><span style="background:{v["hex"]}"></span>{n}'
        f'<code>{v["hex"]}</code></div>' for n, v in palette.items())
    p = palette
    previews.append(f"""<h2>OkSelenized {variant}</h2>
<pre style="background:{bg};color:{p['fg_0']['hex']};padding:1em">
<span style="color:{p['dim_0']['hex']}"># comment: ls output below uses normal + bright ANSI slots</span>
<span style="color:{p['blue']['hex']}">drwxr-xr-x</span>  <span style="color:{p['br_blue']['hex']}">bin/</span>   <span style="color:{p['green']['hex']}">OK</span> <span style="color:{p['br_green']['hex']}">OK-bright</span>
<span style="color:{p['red']['hex']}">error:</span> <span style="color:{p['br_red']['hex']}">bright error</span>  <span style="color:{p['yellow']['hex']}">warn</span> <span style="color:{p['br_yellow']['hex']}">bright warn</span>
<span style="color:{p['magenta']['hex']}">magenta</span> <span style="color:{p['violet']['hex']}">violet</span> <span style="color:{p['cyan']['hex']}">cyan</span> <span style="color:{p['orange']['hex']}">orange</span>
<span style="color:{p['fg_1']['hex']};font-weight:bold">emphasized text</span> on bg_0
</pre>{sw}""")

with open(os.path.join(here, "preview.html"), "w", newline="\n") as f:
    f.write("""<title>OkSelenized</title>
<style>body{font-family:monospace;background:#1a1a1a;color:#ccc;margin:2em}
div span{display:inline-block;width:3em;height:1.4em;vertical-align:middle;margin-right:.6em}
code{margin-left:.6em;color:#888}</style>
""" + "".join(previews))

# Windows Terminal: paste the schemes into settings.json "schemes".
WT_KEYS = ["black", "red", "green", "yellow", "blue", "purple", "cyan",
           "white", "brightBlack", "brightRed", "brightGreen", "brightYellow",
           "brightBlue", "brightPurple", "brightCyan", "brightWhite"]
schemes = []
for variant, pal in palettes.items():
    s = {"name": f"OkSelenized {variant}",
         "background": pal["bg_0"]["hex"], "foreground": pal["fg_0"]["hex"],
         "cursorColor": pal["fg_1"]["hex"],
         "selectionBackground": pal["bg_2"]["hex"]}
    s.update((k, pal[slot]["hex"]) for k, slot in zip(WT_KEYS, ANSI))
    schemes.append(s)
with open(os.path.join(confdir, "windows-terminal.json"), "w",
          newline="\n") as f:
    json.dump({"schemes": schemes}, f, indent=2)

# IntelliJ editor color scheme (.icls). Language schemes inherit from the
# DEFAULT_* attributes, so this small file themes every language.
ICLS_COLORS = [("CARET_COLOR", "fg_1"), ("CARET_ROW_COLOR", "bg_1"),
               ("GUTTER_BACKGROUND", "bg_0"), ("INDENT_GUIDE", "bg_2"),
               ("LINE_NUMBERS_COLOR", "dim_0"),
               ("SELECTION_BACKGROUND", "bg_2"), ("WHITESPACES", "bg_2")]
ICLS_ATTRS = [("DEFAULT_LINE_COMMENT", "dim_0"),
              ("DEFAULT_BLOCK_COMMENT", "dim_0"),
              ("DEFAULT_DOC_COMMENT", "dim_0"),
              ("DEFAULT_KEYWORD", "green"), ("DEFAULT_STRING", "cyan"),
              ("DEFAULT_VALID_STRING_ESCAPE", "br_cyan"),
              ("DEFAULT_NUMBER", "violet"), ("DEFAULT_CONSTANT", "violet"),
              ("DEFAULT_FUNCTION_DECLARATION", "blue"),
              ("DEFAULT_CLASS_NAME", "yellow"),
              ("DEFAULT_INTERFACE_NAME", "yellow"),
              ("DEFAULT_METADATA", "orange"), ("DEFAULT_TAG", "blue"),
              ("DEFAULT_ATTRIBUTE", "green")]
for variant, pal in palettes.items():
    hx = lambda slot: pal[slot]["hex"][1:]
    parent = "Default" if variant == "light" else "Darcula"
    lines = [f'<scheme name="OkSelenized {variant}" version="142" '
             f'parent_scheme="{parent}">', "  <colors>"]
    lines += [f'    <option name="{n}" value="{hx(s)}"/>'
              for n, s in ICLS_COLORS]
    lines += ["  </colors>", "  <attributes>",
              '    <option name="TEXT">', "      <value>",
              f'        <option name="FOREGROUND" value="{hx("fg_0")}"/>',
              f'        <option name="BACKGROUND" value="{hx("bg_0")}"/>',
              "      </value>", "    </option>"]
    for n, s in ICLS_ATTRS:
        lines += [f'    <option name="{n}">', "      <value>",
                  f'        <option name="FOREGROUND" value="{hx(s)}"/>',
                  "      </value>", "    </option>"]
    lines += ["  </attributes>", "</scheme>", ""]
    with open(os.path.join(confdir, f"okselenized-{variant}.icls"), "w",
              newline="\n") as f:
        f.write("\n".join(lines))

print("\nwrote okselenized-{dark,black,light}.json, preview.html,\n"
      "configurations/{minttyrc,icls} per variant, "
      "configurations/windows-terminal.json")
