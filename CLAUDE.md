# CLAUDE.md: shared rules for all PolyKybd repos

This repo holds the instructions and skills that apply to every PolyKybd repo. Attach
it to every session and every environment. Its CLAUDE.md and its skills load like any
other attached repo's.

## Which file to follow

1. **This file** covers rules for all repos: review, branching, mirrored files,
   releases, and the limits of the web session.
2. **The repo's own `CLAUDE.md`** covers only that repo. It does not repeat these rules.
   When the two disagree, the repo file takes priority for that repo.
3. **The docs a CLAUDE.md links** hold the detail and the history behind each rule.
   Read the linked doc before changing that subsystem.
4. **`.claude/rules/*.md`** (path-scoped) load only when the Read tool opens a
   matching file. They do NOT load through `cat`/`sed` in Bash, so they add to a
   CLAUDE.md pointer and never replace one.
5. **Skills** load from every attached repo. The cross-repo skills live here, once.

If this repo is missing from a session, the shared rules are missing too. Ask the user
to attach `thpoll83/polykybd-claude`.

⚠️ **A read-only `add_repo` does not attach it.** For a public repo it only allows an
anonymous clone, at `/home/user/<owner>/<repo>`, and that clone's CLAUDE.md and skills
never load. Attach with `access: "push"`, clone to `/home/user/polykybd-claude` (the
path every repo CLAUDE.md links as `../polykybd-claude`), then call `register_repo_root`.

| dir under `/home/user` | repo | default branch | what it is |
|---|---|---|---|
| `qmk_firmware` | thpoll83/qmk_firmware | `PolyKybd` | firmware (QMK fork, `keyboards/polykybd/`) |
| `PolyKybdHost` | thpoll83/PolyKybdHost | `main` | host app (Python, PyQt5) |
| `polykybd-ctnd` | thpoll83/polykybd-ctnd | `main` | RPi4 hardware-in-the-loop rig + CI runner |
| `polykybd-docs` | thpoll83/polykybd-docs | `main` | public site www.polykybd.org (Astro Starlight) |
| `PolyKybd` | thpoll83/PolyKybd | `master` | hardware: KiCad boards, OpenSCAD/build123d parts |
| `Adafruit-GFX-Library` | thpoll83/Adafruit-GFX-Library | `master` | `fontconvert`, generates the firmware's font headers |
| `wincompose` | thpoll83/wincompose | `main` | WinCompose fork, Unicode input on Windows |
| `gnome-wayland-winreader` | thpoll83/gnome-wayland-winreader | `main` | GNOME Shell extension reporting the focused window (no CLAUDE.md) |
| `polykybd-claude` | thpoll83/polykybd-claude | `main` | this repo |

The old pre-2026-10-10 CLAUDE.md files are kept verbatim in `docs/archive/`. They are
the backstop if a consolidated note turns out to be missing something.

## The web session: what it cannot do

- **You cannot push tags, create a release, delete a remote branch, or create a
  repo.** The git proxy returns 403 on tag refs and branch deletes. There is no `gh`.
  For a release, stage the notes and hand the user `python scripts/publish_release.py`.
  Don't create scratch branches you cannot clean up.
- ⚠️ **The clone is SHALLOW, and `git merge-base` then returns an EMPTY STRING, not an
  error.** A diff against upstream or a tag-anchored range then gives a plausible wrong
  answer. Run `git rev-parse --is-shallow-repository` first;
  `git fetch origin --unshallow --no-recurse-submodules` fixes it.
- ⚠️ **The checkout can be BEHIND what this session pushed, or be reset when the
  container is reclaimed.** Nothing reports it. Before concluding that work is missing,
  or that a review finding does not reproduce: `git log --oneline -1`, then
  `git fetch origin <branch> && git log --oneline HEAD..FETCH_HEAD`. Work you remember
  doing that left no trace is a checkout problem first and a code problem second.
- **Chromium is installed headless** (`/opt/pw-browsers/chromium`, also through
  Playwright). Look at generated HTML, SVG and rendered pages instead of reasoning
  about the markup.
- **`gh api` works for reads** through the proxy, although the session says there is
  no `gh`. A wait for a check run or a review is a bash `until` loop over
  `gh api repos/<owner>/<repo>/commits/<sha>/check-runs` with a timeout, which is how
  a push can wait for CodeRabbit's one included review per hour to finish instead
  of cancelling it (2026-10-20). Writes (release, tag) stay untested.
- **Set the git identity before the first commit**: `git config user.email
  noreply@anthropic.com && git config user.name Claude` in each repo. The stop hook
  rejects an unpushed commit made with the user's address as "unverified" and asks
  for an amend (2026-10-20).
- ⚠️ **A `pkill -f` / `pgrep -f` pattern matches the shell that runs it, and kills it**
  (exit 144, and every step chained after it is lost). The `[x]yz` bracket pattern
  protects only the pattern argument: if the plain text appears anywhere else in the
  same command line, such as a path, the shell still matches. Run `pgrep -af <name>`
  as its own command, then `kill <PID>`.
- ⚠️ **A background command is stopped at its time limit: 30 minutes by default, 2 hours
  at most.** For a job that may run longer (a Blender render, a long build), detach the
  job itself (`setsid nohup bash -c '…; echo EXIT $? >> job.log' &`) and wait with a
  separate `until grep -q '^EXIT' job.log; do sleep 30; done` that has an explicit
  `timeout`. A stopped watcher then costs nothing, because the job keeps running.

Detail and the incidents behind these: [`docs/web-session.md`](docs/web-session.md).

## Branching

- **Start every piece of work on a fresh branch cut from the updated default branch**
  (table above), with a name that says what it is. Once a PR is merged its branch is
  done. A push to it succeeds and orphans the commit.
- ⚠️ **A cross-repo feature can leave one repo with commits pushed and NO PR.** Every
  local check passes on that repo. "Commits ahead" cannot answer it either, since a
  squash-merged branch shows as ahead forever. Only a GitHub query for an existing PR
  can. The `cross-repo-pr-sweep` skill runs it.
- ⚠️ **A merged badge is not proof the work reached the default branch.** Check
  `git merge-base --is-ancestor <head> origin/<default>`, and confirm by content
  (`git cat-file -e origin/<default>:<a file it added>`). A stacked PR merged within a
  minute of its base merges into the base's branch, and neither PR's content reaches the
  default. Recovery is the `re-land-orphaned-pr` skill (in PolyKybdHost).
- ⚠️ **A stacked PR is NOT retargeted when its base merges.** GitHub does that only
  when the base branch is deleted, and merged branches are kept here. Retarget it
  yourself (`update_pull_request base=<default>`), then merge it.
- ⚠️ **A CLAUDE.md merge conflict is either addition beside addition (keep both) or
  supersession (the newer version replaces the older one completely).** After resolving,
  grep each of your notes back by name. Taking the whole of one side silently deletes
  anything that shared the conflict block.

Worked examples, the sweep's fail-open modes and stacked-PR recovery:
[`docs/branching.md`](docs/branching.md).

## Code review

- ⚠️ **Review traffic belongs on the PR, not in the chat** (maintainer's rule,
  2026-10-14: bot events filled the conversation with review text). Handle a
  bot finding, CI result, rate-limit notice or echo of your own reply on the PR, and
  tell the user nothing, or one line. Report only what needs them or ends the round:
  a finding you declined (one line, with why), a blocker, and the end state (merged,
  ready, or red with its cause). Never restate findings, replies or check lists that
  are already on the PR.
- **Ignore CodeRabbit's "Docstring Coverage 80%" check.** It is a CodeRabbit default,
  not project policy, and it does not block. Document new code where it helps a reader.
- **Verify every AI reviewer finding against the code before acting on it.** Several
  arrive confidently wrong, some refuted by their own evidence, and a sound conclusion
  can rest on invented evidence. Fix the true ones. Decline the false ones with the
  counter-evidence on the thread, because CodeRabbit stores a repo learning from it.
- ⚠️ **Name the check you ran, not a stronger one.** "Read the code", "ran the test"
  and "measured on the rig" are different claims. On 2026-10-12 one session said
  "checked by hand" after a code read (qmk#380), "the keymap is correct without a
  reset" when the keycodes had shifted, and called a DOOM job "hung" at 35 min and
  cancelled it. 35 min is that job's normal time. Before calling a job stuck, look up
  its normal duration in the job history.
- ⚠️ **CodeRabbit auto-review is OFF in all PolyKybd repos** (org setting, 2026-10-08).
  Ask with `@coderabbitai review` posted as a COMMENT. The same line in the PR body does
  nothing.
- ⚠️ **A push cancels CodeRabbit's running review** ("Pull request base or head
  changed"), and it does not resume. Re-request on the new head. When bot findings
  arrive minutes apart, fix them in one push per turn rather than one push per finding;
  ctnd#114 lost four CodeRabbit runs this way. The stop hook rejects an unpushed commit
  at the end of a turn, so the batching has to happen within the turn.
- ⚠️ **A green board is NOT evidence anyone reviewed your code.** A quota refusal is a
  review object carrying the head sha, and a clean CodeRabbit pass creates no review
  object at all. Check `get_reviews` and the summary comment's `📥 Commits` range.
  Greptile and Sourcery are out of credit on some repos and still post convincing
  summaries.
- ⚠️ **Raise a new LIMIT with the maintainer before writing it into code or docs**
  (maintainer's rule, 2026-10-09): a cap, bound, ceiling or size. An unmeasured 48-icon (#240)
  cap per app cut Kate's F1, F2 and Find in Files, and two replacements guessed on the
  spot (512, then 1440) repeated the mistake. Say the number, what it counts and what it
  is measured against, then wait. Prefer a value the system already defines (firmware
  `NUM_OVERLAY_SLOTS` = host `OVERLAY_POOL_CAPACITY` = 600).
- ⚠️ **After changing a function signature or renaming a symbol, grep the CLAUDE.md
  files and docs for prose references to it.** Nothing in CI reads Markdown, so a stale
  API example ships and reads as authoritative.
- **Sourcery's `dangerous-subprocess-use-audit` wants `# nosemgrep` plus a written
  audit, not contorted code.** The marker applies only to the line immediately after
  it, so it goes directly above the call, with the reasoning above the marker.
- **Security-scanner findings:** verify each one with the `verify-security-finding`
  skill, and record the disposition in `polykybd-ctnd/docs/SECURITY_AUDIT.md` even when
  nothing changes. A dismissal with no record gets re-raised in full by the next scan.
  In qmk, a finding on an inherited upstream file is a prompt to audit the files we own;
  `qmk_firmware/CLAUDE.md` has the checks.

The detailed guide (which bot stops reviewing and how that looks, merge-commit reviews,
parity pins, worked examples): [`docs/review-conventions.md`](docs/review-conventions.md)
and the `triage-pr-review` skill.

## Writing style

Write docs pages, CLAUDE.md files, skills, PR bodies and review replies in plain,
technical English that a non-native reader can follow (maintainer's rule, 2026-10-15;
docs#131 and docs#133 rewrote all 65 site pages to it).

- **No idioms, metaphors or insider slang.** Write the plain verb: load-bearing →
  required; lands → is written to; wins → takes priority; lives in → is in; carries →
  has; in lockstep → together; escape hatch, gotcha, knobs, ground truth, hard-won,
  quietly, genuinely → say what happens. The full word list is in
  `polykybd-docs/CLAUDE.md` → *Writing style*.
- **No rhetorical questions.** State the point.
- **Cut what the reader does not act on**: design rationale, older-version history, how a
  render was made, and text that repeats the same page.
- Real technical terms (CRC, magic number, backpressure) and product names stay.

## Files kept byte-identical across repos

Nothing in CI compares these copies. Change one, copy it to the others, and run
`bash /home/user/polykybd-claude/.claude/skills/check-mirrored-artifacts/check_mirrors.sh` (the
`check-mirrored-artifacts` skill).

| file | copies | what drift breaks |
|---|---|---|
| `iso_lang_country.py` (frozen, append-only index table) | qmk `keyboards/polykybd/lang/`, host `polyhost/services/`, ctnd `station/` | host and rig decode the wrong languages, silently |
| `publish_release.py` | qmk, host and wincompose `scripts/` | a release gate present in one copy and missing in another. Its tests are in `PolyKybdHost/tests/scripts/publish_release_test.py` |
| `noto-fonts.yaml`, `fontpack_render_settings.json`, `lang_flags.json` | qmk (canonical) → host | the host's font dialogs pre-fill wrong values |
| `quantum/keycodes.h` | qmk → host `polyhost/res/` | the layout editor shows wrong keycode names |

⚠️ **A generated file whose generator's input path no longer exists fails silently, and
no `cmp` catches it.** Re-run the generator (`--check` where one exists) rather than
trusting the file.

## Releases

Every repo releases by **publishing a GitHub Release**, never by pushing a tag. A
pushed tag is placed on the auto-bump `[skip ci]` commit and triggers nothing. Tags:
firmware `PolyKybd-fw-vX.Y.Z`, host `vX.Y.Z`, wincompose `PK-X.Y.Z`. The
`polykybd-github-release` skill drives it.

- ⚠️ **Each `release.yml` refuses a tag whose tree declares a different version.**
  Otherwise the download claims one version, the install reports another, and the
  updater offers the same release forever (wincompose `PK-0.9.19`). The fix is to MOVE
  the tag, and only while no release holds it. Delete the release the refusal left
  behind first.
- ⚠️ **The version increase is label-driven and the label must be set AT OPEN.** It is read
  at merge time, and a label added during the merge arrives too late. A request in the PR
  body is not a label. `create_pull_request` cannot set labels, so call `issue_write`
  with `labels:` right after opening. ⚠️ Then read the labels back a few minutes later.
  The qmk labeler once overwrote `bump:minor`. `issue_write` replaces the list, so
  re-set it in full (`["keyboard","bump:minor"]`).
- ⚠️ **PATCH is the default; `bump:minor` is the exception** (maintainer's rule,
  2026-10-03). Use it only for a feature an owner would call new. A `PROTOCOL_VERSION`
  increase does not imply minor. When unsure, ask.
- ⚠️ **A `PROTOCOL_VERSION` increase means BOTH firmware and host get released, and the
  check is the PUBLISHED versions.** The connect gate is a range, not exact-match, so an
  old host pairs with new firmware and silently leaves the new features off. Publish the
  host first. Host and firmware version numbers are otherwise independent.
- ⚠️ **A docs PR ships the moment it merges; host and firmware ship on a release.** A
  docs page describing new behaviour waits for the release that contains it, or names
  the required version on the page.
- ⚠️ **Write that version only after its bump commit exists on the default branch.**
  Parallel sessions merge in between and take the next numbers. docs#104 named 1.8.6;
  qmk#361 and qmk#364 merged first and took 1.8.7 and 1.8.8, so the feature shipped in 1.8.9
  and the page was wrong until docs#118.

Both repos' original release bullets, verbatim: [`docs/releases.md`](docs/releases.md).

## What costs context

Every attached repo's CLAUDE.md loads in full at session start. An imported file
(`@path`) also loads at launch, so a shared import saves nothing. A linked doc costs
nothing until read, a path-scoped rule until its file is Read, and a skill until it is
invoked. Keep each CLAUDE.md to rules that bind code outside their own subsystem, and
move the rest behind a link. The `prune-claude-md` skill does this without losing a
line. Measurements: [`docs/skills-and-context.md`](docs/skills-and-context.md).

⚠️ **A skill under a subdirectory (e.g. `keyboards/polykybd/.claude/skills/`) does NOT
load.** Skills go at a repo root `.claude/skills/`.
