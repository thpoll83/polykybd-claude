#!/usr/bin/env bash
# Check every file PolyKybd keeps byte-identical across repos.
# Exits non-zero if anything drifted or is missing.
set -uo pipefail

ROOT="${POLYKYBD_ROOT:-/home/user}"
QMK="$ROOT/qmk_firmware"
HOST="$ROOT/PolyKybdHost"
CTND="$ROOT/polykybd-ctnd"
fail=0

check() {  # check <label> <a> <b>
    local label=$1 a=$2 b=$3
    if [ ! -f "$a" ] || [ ! -f "$b" ]; then
        echo "MISSING $label"
        [ -f "$a" ] || echo "         absent: $a"
        [ -f "$b" ] || echo "         absent: $b"
        fail=1
    elif cmp -s "$a" "$b"; then
        echo "ok      $label"
    else
        echo "DRIFTED $label"
        echo "         $a"
        echo "         $b"
        fail=1
    fi
}

echo "--- frozen ISO index table (3 copies) ---"
check "iso_lang_country.py  qmk vs host" \
      "$QMK/keyboards/polykybd/lang/iso_lang_country.py" \
      "$HOST/polyhost/services/iso_lang_country.py"
check "iso_lang_country.py  qmk vs ctnd" \
      "$QMK/keyboards/polykybd/lang/iso_lang_country.py" \
      "$CTND/station/iso_lang_country.py"

echo "--- font manifests (qmk -> host) ---"
check "noto-fonts.yaml" \
      "$QMK/keyboards/polykybd/fonts/noto-fonts.yaml" \
      "$HOST/polyhost/res/fonts/noto-fonts.yaml"
check "fontpack_render_settings.json" \
      "$QMK/keyboards/polykybd/base/fonts/generated/fontpack_render_settings.json" \
      "$HOST/polyhost/res/fontpack/fontpack_render_settings.json"
check "lang_flags.json" \
      "$QMK/keyboards/polykybd/base/fonts/generated/lang_flags.json" \
      "$HOST/polyhost/res/fontpack/lang_flags.json"

echo "--- QMK keycode table (qmk -> host layout editor) ---"
check "keycodes.h" \
      "$QMK/quantum/keycodes.h" \
      "$HOST/polyhost/res/keycodes.h"

echo "--- release script (qmk = host = wincompose) ---"
check "publish_release.py  qmk vs host" \
      "$QMK/scripts/publish_release.py" "$HOST/scripts/publish_release.py"
check "publish_release.py  qmk vs wincompose" \
      "$QMK/scripts/publish_release.py" "$ROOT/wincompose/scripts/publish_release.py"

echo "--- shared skills live ONLY in polykybd-claude ---"
SHARED="$ROOT/polykybd-claude/.claude/skills"
if [ ! -d "$SHARED" ]; then
    echo "MISSING polykybd-claude is not attached: $SHARED"; fail=1
else
    for s in $(ls "$SHARED"); do
        for r in "$ROOT"/*/; do
            [ "$r" = "$ROOT/polykybd-claude/" ] && continue
            if [ -e "$r.claude/skills/$s" ]; then
                echo "STALE   skill $s also in ${r%/} (delete that copy)"; fail=1
            fi
        done
    done
    echo "ok      shared skills checked against every repo under $ROOT"
fi

echo
if [ "$fail" = 0 ]; then
    echo "all mirrors in sync"
else
    echo "DRIFT FOUND — see SKILL.md section 3 before copying either way"
fi
echo "NOTE: this covers COPIES only. Generated artifacts need their generator re-run"
echo "      (SKILL.md section 2) — no cmp can detect a generator whose input path died."
exit $fail
