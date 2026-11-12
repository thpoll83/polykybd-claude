---
name: render-layer-board
description: Render one split72 keymap layer (`_ML`, `_UL`, `_L0`, any `[_XX] = LAYOUT_left_right_stacked(...)` in the default keymap.c) as a picture of the whole board, every keycap showing the legend the firmware draws. Use when designing or reviewing a layer's key placement ("show me the MIDI layer", "what does the utility layer look like now", "preview the layout before I flash"), when the user asks to move keys around and wants to see the result, and for a docs-site picture of a layer. NOT for one keycap or one legend's placement (keycap-layout-preview), the status OLED (status-oled-layout), or a language layout across all keys (add-polykybd-language's renders).
---

# Render a keymap layer as the whole board

`render_layer.py` reads a layer's arguments from the split72 default `keymap.c`, maps
them to matrix positions through `keyboard.json`, renders each key's legend from the
firmware tree, and draws the board with the host's `LangBoard`. The output is what the
keycaps show at rest, before any setting changes.

Legend sources, in this order:

| Keys | Source |
|---|---|
| `QK_MIDI_*` / `MI_*` | the firmware's `midi_legend.c`, compiled and run (`PolyKybdHost/tools/midi_legend_dump.py`; needs a C compiler) |
| letters, digits, punctuation | the language table (`lang_lut.xlsx`) for `--lang` |
| everything else | the two static-text switches: `keycode_helper.c`, then `poly_keymap.c` |

Everything except MIDI goes through `lang_demo.build_frame`, so mod-taps, layer keys
(`MO(_FL)`, `TO(_ML)`) and KC_IME draw as on the board.

## Run it

From `PolyKybdHost` (it needs the host venv and imports the host's `tools/`):

```bash
.venv/bin/python ../polykybd-claude/.claude/skills/render-layer-board/render_layer.py \
    --layer _ML --out /tmp/claude-0/<scratchpad>/ml.png
```

Options: `--lang de-DE` (default `en-US`), `--scale 1.0` (default 0.8, about 1560×535),
`--firmware <qmk checkout>` (default `../qmk_firmware`), `POLYKYBD_HOST=<dir>` for a host
checkout elsewhere.

It prints the size, how many legends it drew, and every key it left dim with its token.
Read that list before showing the picture:

- `_______` and `KC_NO` are dim on purpose.
- `QK_MACRO_*` is dim: the host composes macro keycaps, not the firmware.
- A key whose legend the firmware computes at runtime (`KC_GLYPH_SIZE_UP`, `KC_MRWD`)
  is dim. That is a gap of this model, not a blank key on the board. Say so.
- Anything else dim is a missing legend: check `keycode_helper.c` for its `case`.

Then look at the image (Read it) before you describe it. For the user, send it at
`--scale 1.0`; for the docs site, resize to ~1400 px wide (`polykybd-docs/CLAUDE.md`).

## Iterating on a layout

1. Edit the layer's arguments in `split72/keymaps/default/keymap.c`.
2. Re-run the script and look.
3. ⚠️ **The argument order is the layout order, not visual order.** Left rows 0–2 have 7
   keys each, then `(3,7)` (the encoder, `_______`) and `(3,0..6)`, then `(4,7)`, `(4,0..6)`.
   The right half: `(5,1..7)`, `(6,1..7)`, `(8,0)` (encoder), `(7,1..7)`, `(9,0)`,
   `(8,1..7)`, `(9,1..7)`. When a key lands in the wrong place, print
   `zip(mats, toks)` from the script rather than counting commas.

## Pitfalls

- ⚠️ **`op.OVERSHOOT = 0` is required.** `render_key` draws past the 72×40 panel for
  contact sheets, and the board then fails with `ValueError: images do not match`.
- ⚠️ **Fold token names with the drawable set before `build_frame`.** It calls
  `normalize_kc()` without one, so `KC_MPRV` misses the legend keyed
  `KC_MEDIA_PREV_TRACK` and seven media keys go dim. The script does this.
- **It is a Python model of the C**, like every preview here. For a picture that will be
  published, compare against a photo of the hardware when the draw path changed.
- **The MIDI legends are the resting ones** (octave as PolyKybd sets it, so `MI_C` is
  C4). An octave or transpose change on the keyboard redraws every note key.
- **split72 only.** The board geometry is the host's split72 KLE; split42 has no
  renderer here.
