#!/usr/bin/env python3
"""Render one split72 keymap layer as the whole board, with the legends the firmware draws.

Run with the HOST venv (it imports the host's tools/): from PolyKybdHost,

    .venv/bin/python ../polykybd-claude/.claude/skills/render-layer-board/render_layer.py \
        --layer _ML --out /path/board.png [--lang en-US] [--scale 0.8] [--firmware DIR]

Each key's legend comes from the firmware tree beside the host:
  * QK_MIDI_* / MI_* keys: the firmware's own midi_legend.c, compiled and run
    (PolyKybdHost tools/midi_legend_dump.py, needs a C compiler);
  * letters, digits and punctuation: the language table (oled_preview.render_key);
  * everything else: the two static-text switches (keycode_helper.c, then poly_keymap.c).
A key with none of these (KC_NO, _______, a token nothing draws) is drawn dim and listed.
The encoder positions (3,7) and (8,0) are left out, as on the board.
"""
import argparse
import json
import os
import re
import sys

HOST = os.environ.get("POLYKYBD_HOST", "/home/user/PolyKybdHost")
sys.path[:0] = [HOST, os.path.join(HOST, "tools")]

import lang_demo as ld                      # noqa: E402
import oled_preview as op                   # noqa: E402
op.OVERSHOOT = 0   # render_key draws a border past the panel for contact sheets; the board wants the panel
from kle_render import KeyContent           # noqa: E402
from PIL import Image                       # noqa: E402

LAYOUT = "LAYOUT_left_right_stacked"
ENCODERS = {"3,7", "8,0"}


def layer_tokens(keymap_c: str, layer: str) -> list[str]:
    src = re.sub(r"/\*.*?\*/|//[^\n]*", "", open(keymap_c, encoding="utf-8").read(), flags=re.S)
    m = re.search(r"\[" + re.escape(layer) + r"\]\s*=\s*" + LAYOUT + r"\s*\(", src)
    if not m:
        raise SystemExit(f"no [{layer}] = {LAYOUT}(...) in {keymap_c}")
    depth, start, out = 1, m.end(), []
    for i in range(m.end(), len(src)):
        ch = src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                out.append(src[start:i])
                break
        elif ch == "," and depth == 1:
            out.append(src[start:i])
            start = i + 1
    return [t.strip() for t in out if t.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layer", required=True, help="enum name, e.g. _ML, _UL, _L0")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="en-US")
    ap.add_argument("--scale", type=float, default=0.8)
    ap.add_argument("--firmware", default=os.path.join(os.path.dirname(HOST), "qmk_firmware"))
    a = ap.parse_args()

    qmk = a.firmware
    pk = os.path.join(qmk, "keyboards", "polykybd")
    R = op.load_renderer(os.path.join(pk, "base", "fonts"))
    named = op.load_named_glyphs(os.path.join(pk, "lang", "named_glyphs.h"),
                                 os.path.join(pk, "keycode_helper.h"))
    L = op.Lang(os.path.join(pk, "lang", "lang_lut.xlsx"), named)
    static = {**ld.parse_to_static_text_map(os.path.join(pk, "poly_keymap.c")),
              **ld.parse_static_text_map(os.path.join(pk, "keycode_helper.c"))}
    # Expand the legend macros (MID_TWO_LINE(...) and friends) the way the export does,
    # or build_frame draws the macro's NAME: the record key read "MID_".
    macros = op.parse_function_macros(*(open(os.path.join(pk, f), encoding="utf-8").read() for f in
                                        ("lang/named_glyphs.h", "keycode_helper.h",
                                         "keycode_helper.c", "poly_keymap.c")))
    static = {k: op.expand_function_macros(v, macros) for k, v in static.items()}
    ld.load_qmk_aliases(qmk, pk)

    kh = open(os.path.join(qmk, "quantum", "keycodes.h"), encoding="utf-8").read()
    midi_alias = dict(re.findall(r"\b(MI_[A-Za-z0-9]+)\s*=\s*(QK_MIDI_[A-Z0-9_]+)", kh))
    midi = {}
    try:
        import midi_legend_dump as mld
        midi = mld.midi_legends(pk, log=print) or {}
    except Exception as e:   # an older host without the dump
        print(f"note: no MIDI legends ({type(e).__name__}: {e})")

    toks = layer_tokens(os.path.join(pk, "split72", "keymaps", "default", "keymap.c"), a.layer)
    mats = ld.parse_layout_matrix(os.path.join(pk, "split72", "keyboard.json"))
    if len(toks) != len(mats):
        raise SystemExit(f"{a.layer} has {len(toks)} keys, keyboard.json {len(mats)}")

    # Everything but MIDI through lang_demo.build_frame (mod-taps, wrapped layer tokens,
    # KC_IME, the language table), then the MIDI keys from the firmware's own C.
    # build_frame folds names without the drawable set, so KC_MPRV would miss the legend
    # keyed KC_MEDIA_PREV_TRACK: fold each plain token onto a name we can draw first.
    known = set(static) | set(op.ROW)
    folded = {mp: ld.normalize_kc(t, known) for mp, t in zip(mats, toks)}
    ime = ld.parse_ime_key(os.path.join(pk, "poly_keymap.c"), L.langs)
    frame = ld.build_frame(L, R, folded, a.lang, static, ime=ime)
    for mp, t in zip(mats, toks):
        long = midi_alias.get(t, t)
        if long in midi:
            c = KeyContent()
            c._oled = ld.render_static_cps(R, midi[long])
            frame[mp] = c
    blank = [f"{mp}={t}" for mp, t in zip(mats, toks)
             if mp not in ENCODERS and getattr(frame.get(mp), "dim", False)]
    drawn = len(toks) - len(ENCODERS) - len(blank)

    kle = json.load(open(os.path.join(HOST, "polyhost", "res", "polykybd-split72.json"), encoding="utf-8"))
    rr = ld.LangBoard(kle, unit=104, glyphs=None, bezel=True, margin=12, exclude=ENCODERS, dither=False)
    rr.compact_halves(lambda mp: "L" if int(mp.split(",")[0]) < 5 else "R", gap_px=14)
    img = rr.render_frame(frame)
    if a.scale != 1.0:
        img = img.resize((int(img.width * a.scale), int(img.height * a.scale)), Image.LANCZOS)
    img.save(a.out)
    print(f"{a.out}: {img.width}x{img.height}, {len(toks) - len(blank) - 2} legends, "
          f"{len(blank)} dim: {', '.join(blank)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
