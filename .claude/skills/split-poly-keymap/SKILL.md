---
name: split-poly-keymap
description: Move a group of functions out of the PolyKybd firmware's keys_com/poly_keymap.c (or split one large function there) into its own keys_com/ file without changing behaviour, and land several such moves as parallel PRs. Use when asked for "the next refactoring targets", "make poly_keymap.c smaller", "move X out of poly_keymap.c", "split housekeeping_task_user / process_record_user / ...", or to plan, brief, check and merge a batch of these moves. Covers the function-size survey, the functions that tools parse and must stay, moving state with its only users, the one-block header rule, the moved-line check, the .text comparison, the agent brief, and the serial merge of sibling PRs that all edit the same files. NOT for extracting a reusable community module (that is extract-qmk-module) and NOT for changing behaviour.
---

# Split poly_keymap.c

`keyboards/polykybd/keys_com/poly_keymap.c` held most of the firmware's keymap code
(5271 lines on the morning of 2026-11-23). The moves of that day (qmk_firmware #456,
#458–#460, #462–#470) take it to about 1700 lines once all of them merge. This skill is
the procedure they used.

## 1. Survey

Run from `keyboards/polykybd/` at the updated `origin/PolyKybd`:

```bash
python3 - <<'EOF'
import re
L=open('keys_com/poly_keymap.c').read().split('\n'); res=[]; start=None
for n,l in enumerate(L):
    m=re.match(r'^(?:static\s+)?(?:inline\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\(',l)
    if start is None and m and not l.startswith(('typedef','#','//',' ','\t')) and not l.rstrip().endswith(';'):
        start=n; name=m.group(1)
    elif start is not None and l.startswith('}'):
        res.append((n-start+1,start+1,name)); start=None
for r in sorted(res, reverse=True)[:25]: print(r)
EOF
```

It relies on the file's style: a top-level function's closing `}` is in column 0.
Group the functions by what they do (board init, key path, render helpers, suspend
and wake, display sync, RGB). A group is one PR.

## 2. What must stay in poly_keymap.c

Four tools parse the file by name. A moved function breaks its parser without an error.

| keep here | read by |
|---|---|
| `update_displays()`, `kdisp_idle()` | `dev/tools/check_disp_index.py` |
| `to_static_text()` | PolyKybdHost `scripts/export_preview_data.py` |
| `poly_ime_family()` | `export_preview_data.py` and `render-layer-board`'s `render_layer.py` |
| `glyph_script_blocks[]` | the `add-glyph-script` skill |

Re-check the list before a survey: `grep -rn 'poly_keymap\.c' --include=*.py` in
qmk_firmware, PolyKybdHost and polykybd-claude.

Moving one of these is a cross-repo change (the parser moves too). Ask the maintainer.

## 3. The move

- Same code, same call order, same comments. A comment stays with its code; fix one
  that says "above/below" or names the old file.
- Move a `static` variable with its only users. Make a function or variable shared
  only when both files need it, and declare it in `poly_keymap_internal.h`.
- One declaration block per PR, at the end of `poly_keymap_internal.h`, with a comment
  naming the new file. One entry in `POLY_SRC` (`rules.mk`). One entry in
  `keys_com/README.md`. This keeps the conflicts between sibling PRs small.
- An early `return` in a split function becomes a helper that returns `bool` ("end this
  pass"), as `fw_apply_tick()` (#460) and the phases of #462 and #469.
- Include only the headers the new file uses. Do not copy an include block: #462
  carried an unused `LTR559_LOG_MS` into two files that way.
- `fonts/gfx_used_fonts.h` defines the font arrays. A second file that includes it
  fails to link with "multiple definition". Export what it needs from poly_keymap.c
  instead (#470: `resident_font_count`).
- A QMK weak override (`keymap_key_to_keycode`, `process_record_user`, ...) keeps its
  exact signature.

## 4. Check

```bash
cd <worktree>
export QMK_HOME=$PWD PATH="/root/.qmk_venv/bin:$PATH"
for kb in split72 split42; do
  qmk compile -kb polykybd/$kb -km default && arm-none-eabi-size .build/polykybd_${kb}_default.elf | tail -1
done
python3 keyboards/polykybd/dev/tools/check_disp_index.py
python3 /home/user/polykybd-claude/.claude/skills/split-poly-keymap/check_moved_lines.py \
    origin/PolyKybd keyboards/polykybd/keys_com/poly_keymap.c keyboards/polykybd/keys_com/<new>.c \
    keyboards/polykybd/keys_com/poly_keymap_internal.h
```

- `check_moved_lines.py` lists every removed line it cannot find. Each one must be a
  line you changed on purpose (a reworded comment, `return` → `return true`). Name them
  in the PR body.
- Report the `.text` change for both boards. Lost inlining across the file boundary
  costs 0–80 bytes. More than about 200 bytes means a hot helper stopped being inlined:
  leave it in place and say why.
- No unit test suite compiles `poly_keymap.c` or the `keys_com/` files. The HIL run on
  the PR is the behaviour check. A PR that moves suspend, wake or reboot code also gets
  the `hil-fwapply` label.
- In a fresh `git worktree`, the `lib/` submodule directories are empty and
  `qmk compile` fails. Symlink each empty `lib/<x>` to `/home/user/qmk_firmware/lib/<x>`
  and never stage the symlinks (`git add` with explicit paths).

## 5. Several moves at once

One agent per group, each in its own worktree from the same `origin/PolyKybd` commit.

- ⚠️ **Give every symbol to exactly one group in the brief.** On 2026-11-23 the RGB group
  (#465) and the key-path group (#468) both moved the `RM_*` repeat code, to two
  different files. The second merge had to drop one copy.
- Tell the agents not to request reviews. CodeRabbit gives one review per hour; queue
  the requests yourself, one PR per hour.
- The brief used on 2026-11-23 is the shared-brief section below. Add the group's
  function list, worktree, branch and PR title.

## 6. Merge the sibling PRs

All of them edit `POLY_SRC`, the README list and the end of `poly_keymap_internal.h`,
and most edit `poly_keymap.c` near each other.

1. Merge one PR when every check on its head is green, HIL included.
2. Merge `origin/PolyKybd` into the next PR only. Resolve each hunk on its own:
   - `POLY_SRC`, README, header: keep both sides; remove a declaration both PRs added.
   - `poly_keymap.c`: in a hunk where one side has already moved the code out, take
     the moved-out side. ⚠️ Taking one side for the whole file kept a block #465 had
     already moved to `rgb.c`, and the build failed with "static declaration of
     `flash_rgb_tick` follows non-static" (#468).
3. Build both boards, run `check_disp_index.py`, push, wait for green, merge. Repeat.

This costs one extra HIL run per PR. Merging the PRs without that step merges code
combinations that nothing built.

## Shared brief for an agent

```
Move one group of functions out of keyboards/polykybd/keys_com/poly_keymap.c into a
new file keys_com/<file>.c. Worktree <path> (detached at origin/PolyKybd <sha>),
branch <branch>, PR title <title>.
Your group: <exact function list, and the state only they use>. Siblings move other
groups at the same time; touch nothing else.
Follow /home/user/polykybd-claude/.claude/skills/split-poly-keymap/SKILL.md §2–§4.
Open the PR against PolyKybd with the repo's template, label bump:patch (read it back).
Post no review request, do not merge, do not subscribe.
Report: PR URL, commit, what moved, what became shared, poly_keymap.c lines
before/after, .text change on both boards, the check_moved_lines.py result.
```

## Pitfalls

- A move that also "cleans up" is two changes. Keep the cleanup for a later PR.
- `check_disp_index.py` checks only two functions. It does not prove the other three
  parsed names are still in place; grep for them.
- J-Bot reads `.github/copilot-instructions.md`. Before qmk_firmware#472 it reported
  "retarget to `develop`" on these PRs; decline that if it comes back.
- A PR body written before a sibling merged can describe code that is now elsewhere
  (#468's README entry still named the RGB repeat state after #465). Fix such text in
  the next merge commit.
