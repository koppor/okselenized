# OkSelenized

[Selenized](https://github.com/jan-warchol/selenized) re-derived in the
[Oklab](https://bottosson.github.io/posts/oklab/) color space — the theme
[OkSolar](https://meat.io/oksolar) would have been if it had started from
Selenized instead of [Solarized](https://ethanschoonover.com/solarized/).

> **Alternative:** [Everforest](https://github.com/sainnhe/everforest/) — a
> hand-picked warm "forest" palette with dark+light variants (three contrast
> levels each) and ports to nearly every editor and terminal. Different
> philosophy: mood over system — softer, but no bright ANSI tier, narrower
> hue separation, and its light accents sit below 3:1 contrast.
> `preview.html` renders both side by side.

Motivation: [jan-warchol/selenized#121](https://github.com/jan-warchol/selenized/issues/121).
Analysis showed OkSolar keeps only one of Selenized's improvements over
Solarized (uniform accent lightness — and that one it does *better*, in Oklab).
OkSelenized combines both:

| Design decision | From |
|---|---|
| All 8 accents at one uniform **Oklab** lightness (L = 67), chroma gamut-clamped to sRGB | OkSolar |
| Accent hues with wide separation (green is green, not olive; violet ≠ blue) | Selenized |
| Lighter background (Oklab L 33, not Solarized's 27) — less jarring next to bright windows | Selenized |
| Real bright accent tier (`br_*`, +4.5 L) and a conventional ANSI 0–15 mapping — no gray repurposed into a bright slot | Selenized |
| Contrast floors: main text ≥ 6.0 WCAG, comments ≥ 3.2, every accent ≥ 3.5 (enforced by asserts) | Selenized |

Three variants: **dark** (teal background, Oklab L 33), **black** (neutral
near-black, L 21, for OLED / dark rooms), **light** (cream background, L 96,
accents darker than background with an inverted bright tier). Hex values for
black and light are in their JSON files.

## Palette (dark)

| Name | Hex | OKLCH (L C H) | | Name | Hex | OKLCH (L C H) |
|---|---|---|---|---|---|---|
| bg_0 | `#1c3b44` | 33.2 0.040 220.0 | | red / br | `#f25c54` `#ff6e65` | 67 / 71.5, 0.187, 26.4 |
| bg_1 | `#284650` | 37.6 0.040 220.0 | | orange / br | `#d67943` `#e68751` | 67 / 71.5, 0.135, 49.4 |
| bg_2 | `#3d5a63` | 44.7 0.037 220.0 | | yellow / br | `#b4910a` `#c39f27` | 67 / 71.5, 0.135, 90.9 |
| dim_0 | `#7b8b90` | 62.5 0.020 220.0 | | green / br | `#70a843` `#7eb652` | 67 / 71.5, 0.145, 133.3 |
| fg_0 | `#b3bdc0` | 79.2 0.012 220.0 | | cyan / br | `#26ab9e` `#3bb9ac` | 67 / 71.5, 0.110, 185.1 |
| fg_1 | `#cfd7da` | 87.5 0.010 220.0 | | blue / br | `#5097ef` `#5ea5ff` | 67 / 71.5, 0.150, 255.3 |
| | | | | violet / br | `#a480db` `#b18eea` | 67 / 71.5, 0.135, 300.9 |
| | | | | magenta / br | `#d769a9` `#e677b7` | 67 / 71.5, 0.155, 346.2 |

ANSI 0–15: `bg_1, red, green, yellow, blue, magenta, cyan, dim_0, bg_2,
br_red, br_green, br_yellow, br_blue, br_magenta, br_cyan, fg_1`
(Selenized's scheme — bright slots hold bright accents, not grays, so
`ls --color` and friends stay readable.)

## Files

- `okselenized.py` — the generator. The palette is **constructed by rule**
  in OKLCH, not hand-picked; hex values are derived output. Runs its own
  checks (uniform accent L, WCAG floors, sRGB gamut, valid ANSI map) and
  fails loudly if a knob change breaks them.
- `okselenized-{dark,black,light}.json` — generated palettes + ANSI mapping
  (hex and OKLCH).
- `preview.html` — generated swatches + mock terminal output, all variants.
- `apply.py` — applies a palette to the current terminal via OSC escapes:
  `python3 apply.py {black|dark|light}`; run without arguments to list the
  available variants (no config edits; resets with a new tab — handy for
  A/B-ing the variants live).
- `configurations/` — per-application configs, generated (mintty, Windows
  Terminal, IntelliJ) and hand-maintained (oh-my-bash, mc/newt, aptitude);
  see [configurations/README.md](configurations/README.md).

Regenerate everything with:

```sh
python3 okselenized.py
```

No dependencies beyond the Python standard library. The generated files are
kept in sync automatically: a GitHub workflow reruns the generator on every
push that touches `okselenized.py` and commits the result.

## Tuning

Each entry in the `VARIANTS` table of `okselenized.py` carries its own
knobs:

- `accent_l` — uniform accent lightness (67 dark / 65 black / 58 light).
  Raising it gives airier accents but shrinks the sRGB gamut for
  red/magenta (chroma gets clamped).
- `br_delta` — lightness gap of the bright tier (negative on light:
  "brighter" means more contrast there, i.e. darker).
- `chroma_scale`, `floors` — accent saturation and the WCAG minimums the
  self-checks enforce.

## Testing on a real terminal

1. `python3 okselenized.py` — regenerates and self-checks.
2. Open `preview.html` in a browser for a first visual sanity check.
3. Apply the ANSI 0–15 mapping from `okselenized-dark.json` to a terminal
   (e.g. a `foot`/`alacritty`/`kitty` config stanza, or OSC 4 escape
   sequences) with `bg_0` as background, `fg_0` as foreground, `fg_1` as
   bold/bright foreground.
4. Compare against Selenized dark and OkSolar side by side: run
   `ls --color`, a colored `git diff`/`git log`, and something that uses
   bright variants (e.g. `grep --color`, htop). The specific claims to
   verify: bright slots render as brighter accents (not gray), green reads
   as green rather than olive, and comments (`dim_0`) stay legible.

## Configuration for apps

Per-application configs — terminal emulators (mintty, Windows Terminal),
editors (IntelliJ), prompt (oh-my-bash) and TUI apps (mc, newt/whiptail,
aptitude) — live in [`configurations/`](configurations/), each with its
howto in [configurations/README.md](configurations/README.md).

## Status / not yet done

- Variants: dark, black and light exist; Selenized's **white**
  (pure-white background, maximum contrast) would be one more entry in the
  `VARIANTS` table.
- Shipped so far: live application via `apply.py` (any OSC-capable
  terminal) and the configs under `configurations/`. Static configs for
  foot / alacritty / kitty, a full Notepad++ theme, and editor themes
  (vim, VS Code, …) are not written yet — all derivable from
  `okselenized-dark.json`.

## Credits

- [Solarized](https://ethanschoonover.com/solarized/) by Ethan Schoonover — the original design this whole lineage descends from (MIT).
- [Selenized](https://github.com/jan-warchol/selenized) by Jan Warchoł — hues, lightness ladder, contrast targets, ANSI scheme (MIT).
- [OkSolar](https://meat.io/oksolar) — the uniform-Oklab-lightness idea.
- [Oklab](https://bottosson.github.io/posts/oklab/) by Björn Ottosson — the color space (conversion matrices, public domain).
