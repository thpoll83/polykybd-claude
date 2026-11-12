# CLAUDE.md: shared rules for all PolyKybd repos

This repo holds the instructions and skills for every PolyKybd repo. Attach it to every
session and every environment.

## Which file to follow

1. **This file** is the only CLAUDE.md with rules. It loads at every session start.
2. **Each repo's rules are in `docs/repos/<repo>.md` here** (table below). The repo's
   own `CLAUDE.md` is a pointer to that file. Read the file before you build, edit,
   review or release anything in that repo. When it disagrees with this file, it takes
   priority for that repo.
3. **The docs a rules file links** hold the detail and history. Read the linked doc
   before changing that subsystem.
4. **`.claude/rules/*.md`** (path-scoped) load only when the Read tool opens a matching
   file, not through `cat`/`sed` in Bash. They add to a rules file and never replace one.
5. **Skills** load from every attached repo. The cross-repo skills are here, once.
6. **A new rule** for one repo goes in its `docs/repos/<repo>.md`, never back into that
   repo's `CLAUDE.md`. A rule for all repos goes here as one line, with the detail in a
   linked doc.

If this repo is missing, the rules are missing too. Ask the user to attach
`thpoll83/polykybd-claude`. ⚠️ **A read-only `add_repo` does not attach it**: its
CLAUDE.md and skills never load. Attach with `access: "push"`, clone to
`/home/user/polykybd-claude`, then call `register_repo_root`. The auto-mode classifier can
refuse the push attach: [`docs/web-session.md`](docs/web-session.md) → *When the push
attach is refused*.

| dir under `/home/user` | default branch | what it is | rules |
|---|---|---|---|
| `qmk_firmware` | `PolyKybd` | firmware (QMK fork, `keyboards/polykybd/`) | [qmk_firmware.md](docs/repos/qmk_firmware.md) |
| `PolyKybdHost` | `main` | host app (Python, PyQt5) | [PolyKybdHost.md](docs/repos/PolyKybdHost.md) |
| `polykybd-ctnd` | `main` | RPi4 hardware-in-the-loop rig + CI runner | [polykybd-ctnd.md](docs/repos/polykybd-ctnd.md) |
| `polykybd-docs` | `main` | public site www.polykybd.org (Astro Starlight) | [polykybd-docs.md](docs/repos/polykybd-docs.md) |
| `PolyKybd` | `master` | hardware: KiCad boards, OpenSCAD/build123d parts | [PolyKybd.md](docs/repos/PolyKybd.md) |
| `Adafruit-GFX-Library` | `master` | `fontconvert`, generates the firmware's font headers | [Adafruit-GFX-Library.md](docs/repos/Adafruit-GFX-Library.md) |
| `wincompose` | `main` | WinCompose fork, Unicode input on Windows | [wincompose.md](docs/repos/wincompose.md) |
| `gnome-wayland-winreader` | `main` | GNOME Shell extension reporting the focused window | none |
| `polykybd-claude` | `main` | this repo | this file |

All repos are `thpoll83/<dir>`. Older CLAUDE.md versions are in `docs/archive/`.

## The web session

Each rule has its incident and full text in [`docs/web-session.md`](docs/web-session.md).

- You cannot push tags, create a release, delete a remote branch or create a repo (403).
  There is no `gh` for writes. For a release, stage the notes and hand the user
  `python scripts/publish_release.py`. Create no scratch branch unless the user agrees.
- ⚠️ The clone is shallow, and `git merge-base` then returns an empty string, not an
  error. Check `git rev-parse --is-shallow-repository`; fix with
  `git fetch origin --unshallow --no-recurse-submodules`.
- ⚠️ The checkout can be behind what this session pushed, or reset. Before you conclude
  work is missing: `git fetch origin <branch> && git log --oneline HEAD..FETCH_HEAD`.
- ⚠️ A transient 500 is not a capability limit. Retry in a later turn.
- ⚠️ An `add_repo` clone fetches only the default branch, so a pushed branch reads as
  unpushed. Check `git ls-remote origin refs/heads/<branch>`, then
  `git config --add remote.origin.fetch '+refs/heads/<branch>:refs/remotes/origin/<branch>'`
  (`--add`, and no `*` wildcard).
- ⚠️ `merge_pull_request`'s `expectedHeadSha` must be the full 40 characters.
- `gh api` works for reads, including waiting for check runs and re-running a job.
  Chromium is installed headless (`/opt/pw-browsers/chromium`): look at rendered output.
- Before the first commit in each repo: `git config user.email noreply@anthropic.com &&
  git config user.name Claude`.
- ⚠️ A `pkill -f` / `pgrep -f` pattern matches the shell that runs it. Run
  `pgrep -af <name>` as its own command, then `kill <PID>`.
- ⚠️ A background command stops at 30 min (2 h max). Detach a longer job with
  `setsid nohup` and wait on its log with a separate `until` loop.

## Branching

Detail and worked examples: [`docs/branching.md`](docs/branching.md).

- Start every piece of work on a fresh branch from the updated default branch. A merged
  branch is done; a push to it orphans the commit.
- ⚠️ A cross-repo feature can leave one repo with commits pushed and no PR. Only a GitHub
  query finds it: the `cross-repo-pr-sweep` skill.
- ⚠️ A merged badge is not proof the work reached the default branch. Check its changes
  on `origin/<default>` by content. `git merge-base --is-ancestor` answers only for a
  merge commit: a squash-merged head is never an ancestor.
- ⚠️ A stacked PR is not retargeted when its base merges. Retarget it yourself.
- ⚠️ In a merge conflict on a rules file, resolve the conflicting section only, never by
  taking a whole side. Then grep each of your notes back by a short distinct substring.

## Code review

Detail: [`docs/review-conventions.md`](docs/review-conventions.md) and the
`triage-pr-review` skill.

- ⚠️ Review traffic belongs on the PR, not in the chat. Tell the user only a declined
  finding (one line, with why), a blocker, and the end state.
- Ignore CodeRabbit's "Docstring Coverage 80%" check.
- Verify every AI reviewer finding against the code. Fix the true ones. Decline the
  false ones on the thread with the counter-evidence.
- ⚠️ Name the check you ran, not a stronger one ("read the code" is not "ran the test").
  Look up a job's normal duration before calling it stuck.
- ⚠️ Verify your own correction as hard as the finding: its claim is often wider than its
  behaviour. Re-derive any tally from the API before writing it down.
- ⚠️ CodeRabbit auto-review is off. Post `@coderabbitai review` as a comment. A push
  cancels its running review, so push fixes once per turn; hold a fix with
  `git stash push -u` until the review finishes.
- ⚠️ A green board is not a review. Check `get_reviews` and each review's `commit_id`.
  On a host PR that changes Python, read `github-advanced-security[bot]` comments too:
  a green CodeQL check can still have findings.
- ⚠️ Raise a new limit (cap, bound, size) with the maintainer before writing it. Say the
  number, what it counts and what it is measured against. Prefer a value the system
  already defines.
- ⚠️ After renaming a symbol or changing a signature, grep the docs and rules files.
- Sourcery's `dangerous-subprocess-use-audit`: `# nosemgrep` on the line directly above
  the call, with the written audit above the marker.
- Security-scanner findings: the `verify-security-finding` skill, and record every
  disposition in `polykybd-ctnd/docs/SECURITY_AUDIT.md`.

## Writing style

Write docs pages, rules files, skills, PR bodies and review replies in plain, technical
English that a non-native reader can follow (maintainer's rule, 2026-10-15).

- **No idioms, metaphors or insider slang.** Write the plain verb: load-bearing →
  required; lands → is written to; wins → takes priority; lives in → is in; carries →
  has; in lockstep → together; escape hatch, gotcha, knobs, ground truth, hard-won,
  quietly, genuinely → say what happens. The full word list is in
  [`docs/repos/polykybd-docs.md`](docs/repos/polykybd-docs.md) → *Writing style*.
- **No rhetorical questions.** State the point.
- **Cut what the reader does not act on**: design rationale, older-version history, how a
  render was made, and text that repeats the same page.
- Real technical terms (CRC, magic number, backpressure) and product names stay.

## Files kept byte-identical across repos

Nothing in CI compares these copies. Change one, copy it to the others, and run
`bash /home/user/polykybd-claude/.claude/skills/check-mirrored-artifacts/check_mirrors.sh`.

| file | copies | what drift breaks |
|---|---|---|
| `iso_lang_country.py` (frozen, append-only) | qmk `keyboards/polykybd/lang/`, host `polyhost/services/`, ctnd `station/` | host and rig decode the wrong languages |
| `publish_release.py` | qmk, host, wincompose `scripts/` | a release gate missing in one copy (tests: host `tests/scripts/publish_release_test.py`) |
| `noto-fonts.yaml`, `fontpack_render_settings.json`, `lang_flags.json` | qmk (canonical) → host | the host's font dialogs pre-fill wrong values |
| `quantum/keycodes.h` | qmk → host `polyhost/res/` | the layout editor shows wrong keycode names |

⚠️ A generated file whose generator input no longer exists fails silently. Re-run the
generator (`--check` where one exists).

## Releases

Detail and incidents: [`docs/releases.md`](docs/releases.md). The
`polykybd-github-release` skill drives a release.

- Every repo releases by publishing a GitHub Release, never by pushing a tag. Tags:
  firmware `PolyKybd-fw-vX.Y.Z`, host `vX.Y.Z`, wincompose `PK-X.Y.Z`.
- ⚠️ `release.yml` refuses a tag whose tree declares another version. Move the tag, only
  while no release holds it.
- ⚠️ The version increase is label-driven and read at merge. Set the label with
  `issue_write` right after opening, read it back minutes later, and re-set the full list.
- ⚠️ PATCH is the default; `bump:minor` only for a feature an owner would call new.
- ⚠️ A `PROTOCOL_VERSION` increase means both firmware and host get released. Publish
  the host first.
- ⚠️ A docs PR ships when it merges. A page about new behaviour waits for the release, or
  names the version that gets published (the staged `release-notes/<tag>.md` if not out).
- ⚠️ Read the published releases before you write any version:
  `gh api repos/<owner>/<repo>/releases/latest --jq .tag_name`. Before handing over the
  publish command, fold every merge since the last published tag into the notes.

## What costs context

Every attached repo's CLAUDE.md loads in full at session start, and an `@path` import
loads too. A linked doc, a path-scoped rule and a skill cost nothing until used. So the
repo CLAUDE.md files are pointers, and this file keeps one line per rule. Measurements
and the `prune-claude-md` skill: [`docs/skills-and-context.md`](docs/skills-and-context.md).

⚠️ A skill under a subdirectory (e.g. `keyboards/polykybd/.claude/skills/`) does not
load. Skills go at a repo root `.claude/skills/`.
