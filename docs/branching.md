# Branching (all PolyKybd repos)

Merged 2026-10-10 from `qmk_firmware/keyboards/polykybd/BRANCHING.md` and
`PolyKybdHost/docs/branching.md`. The prose is unchanged.

## Branching (all PolyKybd repos)

- **Give every branch a name that hints at its content** (a short descriptive slug, e.g. `claude/fix-slave-layer-after-fw-apply`, not just the auto-generated `claude/<random-scientist>-<id>`) so the branch list reads as a changelog.
- **Always start new work on a FRESH branch cut from the updated default branch — never keep committing to a branch whose PR has already merged.** Once a PR is merged, that branch is done: `git fetch origin PolyKybd` then `git checkout -b claude/<new-slug> origin/PolyKybd` for the next change. Cherry-pick only the still-unmerged commits onto the fresh branch if needed. This keeps each PR a clean, focused diff against the current default (**`PolyKybd`** here; `main` in the host/rig repos) and avoids a new PR accidentally re-including already-merged commits.
- ⚠️ **A cross-repo feature can leave one repo with commits PUSHED and NO PR — and
  nothing surfaces it.** A PolyKybd feature routinely spans 4–6 repos (firmware,
  host, docs, rig, AdafruitGFX, hardware), and every "is everything saved?" check
  passes on the repo you forgot: the branch is committed, pushed, in sync with its
  upstream, and `git status` is clean. Only the *absence of a PR* is wrong, and no
  local command looks for that. On 2026-08-22 the legend-size work had four PRs open
  and reviewed while **AdafruitGFX** sat on two pushed commits with none — one of them
  the `fontconvert -o` sign fix that the whole `latinbig` relocation depends on. It
  was found only because the user asked whether anything was left to open.
  **Sweep every repo before calling cross-repo work done** — `git status` is not the
  check; commits-ahead-of-default plus "does a PR exist for this branch" is. Run a
  `git fetch` in each repo first (below), then confirm a PR exists for every repo that
  prints:
  ```bash
  seen=0
  for e in qmk_firmware:PolyKybd PolyKybdHost:main polykybd-docs:main \
           polykybd-ctnd:main Adafruit-GFX-Library:master PolyKybd:master; do
      r=/home/user/${e%%:*}; d=origin/${e##*:}
      [ -d "$r/.git" ] || continue
      git -C "$r" fetch -q --no-recurse-submodules origin \
          || { echo "!! $(basename "$r"): fetch failed - NOT inspected"; continue; }
      git -C "$r" rev-parse --verify -q "$d" >/dev/null \
          || { echo "!! $(basename "$r"): $d missing"; continue; }
      seen=$((seen+1))
      n=$(git -C "$r" rev-list --count "$d"..HEAD)
      [ "$n" != 0 ] && echo "$(basename $r): $n commit(s) ahead of ${d#origin/} — PR?"
  done
  [ "$seen" = 6 ] || echo "!! inspected only $seen/6 repos — result is NOT trustworthy"
  ```
  ⚠️ **Three ways the obvious version of this loop FAILS OPEN — it prints nothing,
  which reads identically to "all clean".** All three were hit writing it (2026-08-24):
  - **`~` is `/root`, not `/home/user`** — `$HOME` is root's in this container, so a
    `~/qmk_firmware` path matches no repo and the loop skips all six in silence. Use
    absolute `/home/user/...`, and keep the `seen` counter so a zero-repo sweep is
    loud rather than reassuring.
  - **`origin/HEAD` is UNSET in every clone**, so auto-detecting the default via
    `git symbolic-ref refs/remotes/origin/HEAD` yields nothing and any `|| origin/main`
    fallback silently reports 0 for the firmware (default `PolyKybd`) and AdafruitGFX
    (`master`). Hence the explicit `repo:default` table.
  - **Without the fetch, stale remote refs cry WOLF the other way** — right after a
    merge, an un-fetched repo still shows the merged branch as ahead of its old
    `origin/main`. That direction is at least visible; the first two are not.
    ⚠️ **A FAILED fetch is a fourth mode, and it is the one that reads as inspected.**
    It cannot fake a clean result — measured, not reasoned: a stale `origin/<default>`
    is *behind* the true remote, so `$d..HEAD` can only count the same or MORE, never
    fewer (post-merge it reports 1 where a fresh ref reports 0). But the repo is then
    compared against unknown-age data while still incrementing `seen`, which is
    precisely what that counter exists to prevent — hence the `|| continue` on the
    fetch, so an unreachable repo trips the `seen` guard instead of passing quietly.
  - ⚠️ **A FIFTH mode, and it is the loop's own blind spot: `$d..HEAD` inspects only
    the branch that happens to be CHECKED OUT.** Anything pushed to another branch is
    invisible, so standing on a merged branch makes the sweep print a clean board for
    a repo that has work sitting on a different one. Measured 2026-09-01: the loop
    reported all six repos clean while this repo's `claude/firmware-feature-gaps-jvp9hz`
    was 13 commits ahead — found only because that branch was restarted for unrelated
    reasons. (Benign in the event: the commits were superseded, their content already
    on `PolyKybd`. But the sweep could not have told me that either way.)
  - ⚠️ **Do NOT "fix" it by sweeping every remote `claude/**` branch — measured, that
    is unusable.** A squash- or merge-merged branch reads as ahead of the default
    forever, so across the five repos there are **525** `claude/*` branches, **95**
    read as "ahead", and only **3** of those had an open PR. A ~95% false-positive
    rate is a check nobody will read twice.
    ```bash
    # what the numbers came from — per repo, count branches vs branches "ahead"
    for b in $(git -C "$r" for-each-ref --format='%(refname:short)' 'refs/remotes/origin/claude/*'); do
        [ "$(git -C "$r" rev-list --count "$d".."$b")" != 0 ] && echo "$b"
    done
    ```
    **So "commits ahead" cannot answer this question at all, on one branch or on all
    of them — the only reliable signal is whether a PR EXISTS**, which is a GitHub
    query and not a git one. That is what this note already prescribes and what the
    loop never implemented; the loop is a cheap prompt to go and check, never a clean
    bill of health. Treat a silent sweep as "nothing obvious on the branch I am
    standing on", nothing more.


## Landing a stacked PR

The orphaned-merge post-mortem (#244/#245) is below, under *More branching rules*.
Two more rules came out of landing #324 → #325 here (2026-10-01):

- ⚠️ **GitHub does NOT retarget the stacked PR when its base merges** — only when the
  base BRANCH is deleted, and merged branches are kept here (the web session's git
  proxy cannot delete one). #325 still read `feature/status-idle-plasma-word` more
  than 20 minutes after #324 merged. Retarget it yourself
  (`update_pull_request base=PolyKybd`), and only merge once `base.ref` reads
  `PolyKybd`.
- **After a SQUASH merge, merging `PolyKybd` into the stacked branch conflicts in every
  file the base PR touched**, because the squash commit is unrelated history. The
  stacked branch already contains the base PR's last head, so the test per file is:

  ```bash
  git diff <base PR's last head> origin/PolyKybd -- <file>   # empty => keep ours
  ```

  Empty means nothing else landed in that file, so the branch's version is right
  (`git checkout --ours`). A non-empty diff is the part to carry over by hand: here
  only `config.h` differed, by the `FW_VERSION` auto-bump. Then confirm
  `git diff --stat origin/PolyKybd` shows exactly the stacked PR's own
  additions/deletions (+374/−104 for #325) before pushing.
- **A stacked PR that is ONE commit on your own branch: rebase it instead.** Skip the
  per-file merge and move the commit:

  ```bash
  git rebase --onto origin/PolyKybd <base PR's last head> <stacked branch>
  diff <(git diff <base PR's last head> <old stacked head>) <(git diff HEAD~1 HEAD) && echo PATCH-SAME
  git push --force-with-lease=<stacked branch>:<old stacked head> origin HEAD:<stacked branch>
  ```

  ⚠️ **Prove it by the PATCH, not the tree.** The default has usually moved past the
  base PR, so `git diff <old stacked head> HEAD` lists every unrelated merge and fails on
  a perfect rebase. Host #328 after #327's squash (2026-10-09): the tree check failed on
  #329/#330's files, and the patch compare was identical.
- **Squashing a branch full of merges before review**: build the squash beside the
  branch and prove it is the tested code before replacing it.

  ```bash
  git checkout -B tmp origin/PolyKybd
  git merge --squash <branch> && git commit      # reuse the feature commit's message
  git diff --quiet <branch> HEAD && echo TREE-SAME
  git push --force-with-lease=<branch>:<old head sha> origin HEAD:<branch>
  ```

  If the squash itself conflicts (a stacked branch over a rewritten base),
  `git read-tree -u --reset <old head>` writes the exact tested tree. Done three times on
  2026-10-09 (#370, host #327, host #328); each result was byte-identical to the head CI
  had tested.


Extracted from `CLAUDE.md` 2026-09-14. The prose is unchanged; only heading levels
and relative links were adjusted to suit a standalone file.

## More branching rules, with worked examples

- **Give every branch a name that hints at its content.** When creating a branch, append a short, descriptive slug describing the change (e.g. `claude/fix-firmware-update-menu-daemon-mode`, not just the auto-generated `claude/<random-scientist>-<id>`). The random scientist/id suffix from Claude Code on the web is auto-assigned server-side and can't always be overridden mid-session, but whenever a branch name is chosen by us, make it self-explanatory so the branch list reads as a changelog.
- **Always start new work on a FRESH branch cut from the updated default branch — never keep committing to a branch whose PR has already merged.** Once a PR is merged, that branch is done: `git fetch origin <default>` (and for the next piece of work `git checkout -b claude/<new-slug> origin/<default>`). Cherry-pick only the still-unmerged commits onto the fresh branch if needed. This keeps each PR a clean, focused diff against the current default (`main` for host/rig, `PolyKybd` for the firmware) and avoids a new PR accidentally re-including already-merged commits.
  - ⚠️ **Violating this is INVISIBLE — a push to a branch whose PR has already
    merged SUCCEEDS and orphans the commit.** git reports an ordinary fast-forward,
    GitHub shows nothing (a merged PR does not reopen, update, or list the new
    commit), and the work is simply not in `main` and not in any PR. It is easy to
    hit without meaning to: the window is "the PR merged while you were still
    working", not "you deliberately reused an old branch" — that is exactly how
    the CLAUDE.md commit from #168 was stranded (2026-08-17, recovered as #171).
    The one check, worth running before reporting any push as done:
    `git merge-base --is-ancestor <sha> origin/main` (and `git log --oneline
    --merges -5 origin/main` to see whether your PR's merge already went in).
    Recovery is the restart above: `git checkout -B <branch> origin/<default>`,
    cherry-pick the orphan, `git push --force-with-lease`, open a NEW PR — expect
    an add/add conflict if another PR touched the same region meanwhile.
- ⚠️ **A CLAUDE.md conflict is one of TWO kinds, and telling them apart matters —
  the second one deletes your work silently if you resolve it the usual way.**
  This file is append-heavy and every branch adds notes at the same anchors, so
  conflicts here are routine (two in 90 minutes on 2026-08-18):
  - **Addition beside addition** — main and your branch each inserted a new note
    at the same anchor. Keep BOTH; put main's first so the diff against main
    stays minimal.
  - **Supersession** — main's PR *implemented* something and rewrote the note
    that said it was impossible (`Browser-URL matching is LOCAL-ONLY` → `…DOES
    cross machines`, #173). Main's version wins **outright**; keeping both ships
    a file that contradicts itself. Verify you contributed nothing to that region
    first — `git show <base>:CLAUDE.md | grep -c "<phrase>"` against your branch
    proves it is inherited, not yours.
  - ⚠️ **After resolving, grep each of your notes back by name.** Taking one side
    wholesale also deletes anything of yours that merely *shared the conflict
    block* — git reports a clean merge, the file has no markers, and the loss is
    invisible. That happened on 2026-08-18: a supersession block also contained
    two unrelated new notes, and "take theirs" removed them. The check is
    `for pat in "<note phrase>" …; do grep -c "$pat" CLAUDE.md; done` — one line,
    and the only thing standing between you and silently dropped work.
    ⚠️ Grep **prose**, not a phrase containing markup: this file wraps identifiers
    in backticks, so a pattern typed as `crash_summary() puts the crash counts`
    scores 0 against a line reading ``` `crash_summary()` puts the crash counts ```
    — a false "note lost" scare mid-resolution (2026-08-18). Pick a distinctive
    run of plain words, or include the backticks.
  - ⚠️ **The same grep-back is the check for a SCRIPTED edit, not just a merge —
    and there it catches a different cause.** Editing this file with a
    `s.replace(anchor, new)` drops whatever sits between the two when the
    replacement does not repeat the anchor's opening lines verbatim: python does
    exactly what it was told, nothing errors, and the file reads fine because the
    surviving text still forms a sentence. That is how a line vanished on
    2026-09-01 — the anchor began *"bot) does not re-raise it…"* and the
    replacement began one line lower, so that clause was silently deleted from a
    note being extended, not rewritten. Assert the anchor count before writing
    (`assert s.count(anchor) == 1`), then grep each note back by name afterwards.
    The merge case and this one share nothing but the remedy, which is the reason
    to state it once for both.


## Worked example: a merged PR whose work never reached `main` (2026-09-19)

The rule in `CLAUDE.md` says a **push** to a merged branch orphans the commit.
A **merge** does it too, and the stated check does not fire, because nothing was
pushed.

Two stacked PRs, eight seconds apart:

```
15:37:09  #244 merged -> main
15:37:17  #245 merged -> claude/mac-duplicate-host-icons-phqu7w
```

#245 was based on #244's branch. GitHub retargets a stacked PR to the base's own
base only when the base BRANCH is deleted (see Preventing it) — not on the merge,
and not within eight seconds, so #245 merged into a
branch that was itself already merged and closed. **Both PRs read "merged".**
Neither GitHub nor git reported anything wrong. None of #245's work was on
`main`:

```bash
$ git merge-base --is-ancestor b98445b origin/main
b98445b: NOT ON MAIN
$ git cat-file -e origin/main:polyhost/util/filelock.py
filelock.py: ABSENT from main
```

### Why the obvious fix is wrong

The orphan branch was cut before PR #243, so `git diff --stat origin/main
origin/<orphan>` showed **606 deletions** of work that had landed meanwhile —
the idle-timeout feature, `command_ids.py`, `poly_kybd.py`, two version bumps.
Merging it would have reverted all of that to recover 558 lines. By the time an
orphan is noticed it is nearly always too stale to merge.

### The recovery

The orphaned PR's own diff is recoverable exactly, because its base head is on
`main` already:

```bash
git checkout -B <new-branch> origin/main
git diff <pr-base-head> <pr-head> | git apply --3way
```

Here `git diff 45e5bce b98445b` reproduced exactly the 8 files and 558/53 GitHub
had shown for #245, and the 3-way apply kept main's newer `CLAUDE.md` sections
from #243 and #244 rather than reverting them.

⚠️ **Verify against the WORKING TREE, not `HEAD`.** `git apply` stages without
committing, so `git diff <pr-head> HEAD` compares against the branch point and
reads as total content loss — a minute of panic, every time. The right form
takes no second ref:

```bash
git diff <pr-head> -- <the PR's files>      # expect output only where main moved
```

Then grep every note back by name, both directions — the re-landed PR's and the
ones `main` gained while it was orphaned. A 3-way apply that quietly dropped one
side looks identical to one that did not.

The whole procedure, including how to tell an orphan from a PR that simply has
not merged, is the **`re-land-orphaned-pr`** skill.

### Preventing it

Merge the base. Retarget the stacked PR to the default branch yourself
(`update_pull_request base=main`, or *Edit* next to the PR title). Check that its
`base.ref` reads the default branch, then merge it. Merging both inside a minute
is the whole bug.

⚠️ **Do not wait for GitHub to retarget it.** GitHub moves a PR off its base
only when the base BRANCH is deleted, and this repo keeps merged branches (the
web session's git proxy cannot delete one either). On 2026-10-01 #300 merged at
13:48, and #301 still read `feature/brave-einstein-p706yi` minutes later; it was
retargeted by hand. A rule that says "wait for `base.ref` to change" waits
forever here.

⚠️ **A stacked PR also gets no CodeQL until it targets `main`** — see
`review-conventions.md`. Expect a first round of findings right after the
retarget, and budget for it before the merge.

### After a squash-merged base: merging `main` into the stacked branch

Squashing the base PR puts unrelated history on `main`, so merging `main` into the
stacked branch conflicts in every file the base PR touched. The stacked branch already
contains the base PR's last head, so decide each file by what ELSE landed in it:

```bash
git diff <base PR's last head> origin/main -- <file>   # empty => keep ours
```

Empty means only the base PR changed the file and the branch's version is right
(`git checkout --ours`); anything else is the part to carry over by hand. Then check
that `git diff --stat origin/main` shows exactly the stacked PR's own
additions/deletions before pushing. Seen on the firmware's #324 → #325 (2026-10-01):
seven conflicted files, of which only `config.h` differed, by the version auto-bump,
and the result matched the PR's +374/−104.

### A stacked PR that is ONE commit on your own branch: rebase it instead

When the stacked branch is yours and carries a single commit, skip the per-file merge
and move the commit:

```bash
git rebase --onto origin/main <base PR's last head> <stacked branch>
diff <(git diff <base PR's last head> <old stacked head>) <(git diff HEAD~1 HEAD) && echo PATCH-SAME
git push --force-with-lease=<stacked branch>:<old stacked head> origin HEAD:<stacked branch>
```

⚠️ **Prove it by the PATCH, not the tree.** `main` has usually moved past the base PR by
then, so `git diff <old stacked head> HEAD` lists every unrelated merge and fails even
on a perfect rebase. #328 after #327's squash (2026-10-09): the tree check failed on
#329/#330's files, and the patch compare was identical.

### Squashing a branch full of merges before review

Build the squash beside the branch and prove it is the tested code before replacing it:

```bash
git checkout -B tmp origin/main
git merge --squash <branch> && git commit      # reuse the feature commit's message
git diff --quiet <branch> HEAD && echo TREE-SAME
git push --force-with-lease=<branch>:<old head sha> origin HEAD:<branch>
```

If the squash itself conflicts (a stacked branch over a rewritten base),
`git read-tree -u --reset <old head>` writes the exact tested tree, and the commit then
holds precisely that. Done three times on 2026-10-09 (#327, #328, qmk#370); each result
was byte-identical to the head CI had tested.
