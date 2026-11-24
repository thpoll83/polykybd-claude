---
name: add-fuzz-target
description: Add a libFuzzer target for a PolyKybd firmware parser to keyboards/polykybd/dev/fuzz/ end to end — the entry point and its exact-model checks in poly_fuzz.c, the Makefile, seeds from the googletest fixtures (make_seeds.py), the googletest replay suite, the polykybd-fuzz.yml job list, manual-run options and paths:, the README — and prove every check by breaking the parser on purpose. Use when asked to "fuzz <parser>", "add a fuzz target / harness", "cover cmd NN with the fuzzer", after adding a parser that reads host, split-link or flash bytes, or when a review says a harness check is too loose. NOT for host Python fuzzing (PolyKybdHost tests/fuzz, Hypothesis) and NOT for triaging a crash a fuzzer found (dev/fuzz/README.md → "When a fuzzer finds a crash").
---

# Add a fuzz target

The firmware fuzz setup has one entry point per target in `poly_fuzz.c`, a shared
libFuzzer `main` (`fuzz_main.c`), and four other places that must list the target. A target
missing from any of them builds locally and then is not run in CI, not replayed, or not
triggered by the files it covers. Done for 5 targets in qmk#476 and 6 in qmk#480; the
reviews on those PRs found every failure mode listed under Pitfalls.

Paths are relative to `qmk_firmware/`. Read `docs/repos/qmk_firmware.md` → *Fuzzing* first.

## 0. Pick the parser and read it

- The input must be bytes someone else controls: a HID report, a split-link frame, a
  flash/EEPROM blob. Note every length, offset, count and index it reads.
- It must build on the host. A parser with a googletest in `base/tests/` or
  `features/*/tests/` already does, so start from that test's sources and stubs.
- Note what it returns on refusal and every output parameter it writes.

## 1. Entry point and checks (`dev/fuzz/poly_fuzz.c`, `poly_fuzz.h`)

```c
int poly_fuzz_<name>(const uint8_t *data, size_t size);   // POLY_FUZZ_OK or the failed check's number
```

- **Exact-size buffers.** Copy the input into its own allocation of exactly the length the
  parser is told (`dup_exact`, `xmalloc`, `xcalloc`; they abort on OOM). ASan then reports
  a one-byte overrun. For report parsers, pass `length` equal to the buffer size.
- **Checks compare against a model, not a bound.** For each output: the exact value it
  must have (decoded independently in the harness), the exact offset (scan for it), the
  exact state transition. "In range" or "at most N" passes when the function does
  nothing.
- **Refusals leave every output unchanged.** Pre-fill each output with a sentinel and
  compare after a refusal. A `bool` output has no third value: parse the refused input a
  second time with the opposite starting value.
- **Number the checks** (`rc = 1`, `rc = 2`, ...) and give each a comment saying the
  rule. `fuzz_main.c` prints `invariant N broken` and aborts.
- If the parser takes a board geometry, run every input with split72 (10×8) and split42
  (8×6), and say in a comment that the values are copied from the variants' `config.h`.

## 2. Makefile, seeds, replay

- `dev/fuzz/Makefile`: add the target to `TARGETS` and its new `.c` files to `SRC`.
  `HDRS` comes from `clang -MM` and updates itself.
- `dev/fuzz/make_seeds.py`: build 3–6 valid seeds from the googletest fixtures (one per
  op or branch) into `corpus/<name>/`, with descriptive names. Re-run it and check that
  the corpus does not change.
- `base/tests/fuzz_replay_tests.cpp`: add the target to the target list (corpus replay,
  2000 mutated and 2000 random inputs). Add the new `.c` files to
  `base/tests/test_rules.mk`.

## 3. Workflow and README

- `.github/workflows/polykybd-fuzz.yml`: add the target to the matrix list and to the
  `workflow_dispatch` options, and add every new source **and header** to `paths:`. Then:
  ```bash
  python3 /home/user/polykybd-claude/.claude/skills/add-fuzz-target/check_fuzz_paths.py
  ```
  It checks every Makefile `SRC`+`HDRS` file against `paths:`, that every `paths:` entry
  matches a file, and that the matrix and options equal `TARGETS`. Exit 0 = OK.
- `actionlint .github/workflows/polykybd-fuzz.yml`.
- `dev/fuzz/README.md`: a row in the target table with what it covers and the input
  layout. More targets also lengthen the Wednesday/Sunday run (targets × 5 h); say so in
  the PR body.

## 4. Run, then prove the checks

```bash
cd keyboards/polykybd/dev/fuzz
make CC=clang-18 -j4                                  # all fuzzers, no warnings
./build/fuzz_<name> -max_total_time=120 /tmp/c_<name> corpus/<name>   # scratch dir FIRST
```

Then break the parser once per check that matters, run the fuzzer 30–40 s on a scratch
corpus, and expect it to stop on that check (`invariant N broken`) or on ASan. Restore the
parser after each one (copy it to a backup first). Mutations that map to real mistakes:

| mutation | expected |
|---|---|
| read one byte past the input | ASan heap-buffer-overflow |
| make a matcher/updater a no-op | the exact-model check for its output |
| return the "end"/refusal result unconditionally | the check that END/refusal happens only when the bytes call for it |
| off-by-one in a bounds check | the bounds check, or ASan |
| write an output before refusing | the "refusal leaves outputs unchanged" check |

The `mutation-test-suite` skill (§2c) has the general method.

Finally, from the repository root:

```bash
PATH=/root/.qmk_venv/bin:$PATH make test:polykybd_fuzz_replay      # and the parser's own make test:<suite>
git status --short keyboards/polykybd/dev/fuzz/corpus             # must list only your named seeds
```

and cppcheck on `dev/fuzz/` with the flags `.github/workflows/cppcheck.yml` uses.

## Output

The PR body: a table of target → functions → input layout, the 120 s run counts, each
mutation and the check that caught it, the commands above with results, and the change in
fuzz jobs per PR and scheduled runner-hours. Label `bump:none` when no parser source
changed.

## Pitfalls

- ⚠️ **A fuzzer writes new inputs into the FIRST corpus folder it is given.** Never pass
  `corpus/<name>` first; clean `corpus/` before committing (35 SHA-named files on qmk#480).
- ⚠️ **A missing header in `paths:` means a PR changing it runs no fuzz job** (five were
  missing on qmk#477). Run `check_fuzz_paths.py`; do not compare by eye.
- ⚠️ **A bound-only check is the most common harness bug.** J-Bot found seven on qmk#480:
  an unchecked second output on refusal, slots checked for range but not value, a matched
  mask checked for extra bits but not missing ones, a find result checked for "after some
  NUL" instead of the id-th one, END accepted anywhere, ring updates checked only against
  an upper bound.
- ⚠️ **A mutation can be caught by a different check than the one you meant.** A byte-order
  swap in a shared helper broke the validation check (1), not the decode check (2). Mutate
  only the function under test to prove a specific check.
- The root `.gitignore` excludes Makefiles under `keyboards/`; a new Makefile needs
  `git add -f` (see `docs/repos/qmk_firmware.md`).
