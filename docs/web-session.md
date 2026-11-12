# The web session's checkout: stale, behind, or reclaimed

_Moved verbatim from `PolyKybd/CLAUDE.md` on 2026-10-10._

⚠️ **`git fetch` your own branch before concluding that work is missing — the
container's checkout can sit BEHIND what this same session already pushed, or be
reclaimed outright.** Three forms, in rising order of nastiness. (1) The tree is one
commit old and perfectly self-consistent, so a round that *was* implemented, committed
and pushed reads as not done — `grep` finds none of its identifiers and the natural
"my scripted edit matched nothing" explanation is plausible enough to write up as a
lesson. It was wrong, and the whole round was rebuilt before `git push` rejected the
duplicate. (2) The same staleness silently invalidates the EXPERIMENT you run to check
a review finding: a Makefile finding was reproduced twice as *not* reproducing, because
the test exercised the old rule. (3) The container is reclaimed and the branch head is
not in the object store at all — `git log` shows an unrelated commit under your own
branch name. Three habits:

- `git fetch origin <branch> && git log --oneline HEAD..FETCH_HEAD` **before** starting
  work, and again before diagnosing anything as absent.
- Treat "work I remember doing has left no trace" as a *checkout* hypothesis first and a
  *code* hypothesis second. Absent work leaves no fingerprints; failed work leaves some.
- **Before reporting a finding as non-reproducing, confirm the code you just ran is the
  code the finding is about** — `git log --oneline -1` plus a grep for the quoted line.
  `git show <sha>:<path>` answering *"fatal: invalid object name"* for your own commit
  is the unambiguous version of the signal.

## Killing a process without killing your own shell

_Added 2026-10-10, from the PCB render session._

`pkill -f` and `pgrep -f` match the full command line of every process, including the
shell that is running them. The usual guard is a bracket in the pattern
(`pgrep -f "[b]lender"`): the regex `[b]lender` matches the text `blender` but not the
text `[b]lender`, so the pattern does not match itself. It only protects the pattern,
though. In `pgrep -f "[b]lender-5.1.2" | xargs kill` run beside a command that names
`/tmp/blender-5.1.2-linux-x64/blender`, the shell's own command line contains the plain
text, so it matches, and the shell kills itself with exit 144. The same happened with a
plain `pgrep -f blender-5.1.2-linux | xargs -r kill`. It happened twice in one session,
and `polykybd-docs` had recorded the `http.server` form of the same trap on 2026-10-01
and 2026-10-09.

The safe form is two commands: `pgrep -af <name> | grep -v pgrep` to list, then
`kill <PID>` with the numbers it printed.

## Jobs longer than a background command's time limit

A background Bash command is stopped when it reaches its `timeout`: 30 minutes when none
is given, 2 hours at most. A 2800 px Cycles render of a PCB took 45 to 62 minutes, so a
render started as a plain background command would have been killed partway through.

What worked:

```bash
# the job, detached from the tool call; its log records how it ended
setsid nohup bash -c "blender -b … > job.log 2>&1; echo EXIT \$? >> job.log" > /dev/null 2>&1 &
# a separate watcher, as a background command with an explicit timeout (ms)
until grep -q '^EXIT' job.log; do sleep 30; done; grep -E '^EXIT|Saved' job.log
```

Four watchers reached their limit that session while their renders kept running, and the
renders were picked up afterwards from `job.log`. When a watcher is stopped, check the
job with `pgrep -af` and the log's modification time before concluding it died.

## Reading a Linux package's files without installing it

The Ubuntu archive is reachable through the proxy, so the files a package ships
(desktop entries, D-Bus service files, icons) can be read in the container before
code depends on them:

```bash
mkdir -p /tmp/pkg && cd /tmp/pkg
apt-get download gnome-terminal          # warns "unsandboxed as root": harmless
dpkg-deb -x gnome-terminal_*.deb x
find x -name '*.service' -o -name '*.desktop'
```

Name the package version as evidence in the PR. PolyKybdHost#578 (2026-11-05) read
`org.gnome.Terminal.service` from gnome-terminal 3.52.0-1ubuntu2 to confirm that its
`Exec=` is `/usr/libexec/gnome-terminal-server` before matching on it.

⚠️ **`apt-get install` puts no translation files on disk here.** The image drops
`/usr/share/locale` on install, so `libkf5configwidgets-data` installed cleanly and
left no `.mo` files. `apt-get download` + `dpkg-deb -x` keeps them. For a check of
UI translations, Ubuntu's `language-pack-gnome-<lang>-base` packages
(`zh-hans`, `zh-hant`; `pt` includes `pt_BR`) hold about 200 real catalogs per
language: GTK3 and the GNOME apps, beside KDE's `libkf5configwidgets-data` and
`libkf5xmlgui-data`. The proxy refuses `gitlab.gnome.org`, so the GNOME `.po`
sources cannot be fetched instead. PolyKybdHost#639 (2026-11-06) checked its
shortcut-label phrases against 4,219 such catalogs
(`tools/shortcut_lexicon_verify.py` says how).

## When the push attach is refused

On 2026-11-04 the auto-mode classifier refused `add_repo` with `access: "push"` for
this repo twice, with no reason given. `access: "read"` still worked: it gives an
anonymous clone at `/home/user/thpoll83/polykybd-claude`.

- Open a skill's `SKILL.md` from that clone with the Read tool and follow its steps
  yourself. Its skills are not available through the Skill tool.
- Nothing can be pushed from that clone. Write a change for this repo as a patch file
  in the scratchpad and give the user its path.
- The user can allow the attach. On 2026-11-05 the user asked for it directly and the
  same `add_repo` call succeeded; the patch was then applied as polykybd-claude#17.

## When resolving a review thread is refused

On 2026-11-07 the auto-mode classifier refused
`gh api -X POST repos/<owner>/<repo>/pulls/<n>/ccr/comments/<id>/resolve` as an
external write ("External System Writes"). The four threads on PolyKybdHost#683 were
finished: the maintainer had declined each finding and CodeRabbit had accepted.

- Reading threads works: `gh api repos/<owner>/<repo>/pulls/<n>/ccr/review_threads`
  lists each thread with `resolved` and its `comment_ids`.
- `mcp__github__resolve_review_thread` is the other route. It was not tried on these
  threads, so it is not known whether the classifier allows it.
- When neither works, list the open threads in your report and leave them to the user.
  An unresolved thread does not block a merge here.

## A job cancelled after 15 minutes with no log

On 2026-11-11 qmk#427's "PolyKybd unit tests" and the PR labeler both showed
`cancelled` after exactly 15 minutes (21:38:50 → 21:53:51). GitHub had never given
either job a runner. Three signs tell this apart from a cancelled test:

- the job's `runner_name` is empty (`gh api repos/<owner>/<repo>/actions/jobs/<id>`);
- its log returns `BlobNotFound` (HTTP 404), because no step ever ran;
- no step has a conclusion.

Re-run it once: `gh api -X POST repos/<owner>/<repo>/actions/runs/<run-id>/rerun-failed-jobs`
(the run id, not the job id). On qmk#427 the re-run got a runner and passed. This is
not the rig: a self-hosted HIL job that cannot start stays `queued` instead
(`qmk_firmware/CLAUDE.md`).

## The full rules, moved from CLAUDE.md on 2026-11-12

`CLAUDE.md` keeps a one-line version of each rule below and links here.

### The web session: what it cannot do

- **You cannot push tags, create a release, delete a remote branch, or create a
  repo.** The git proxy returns 403 on tag refs and branch deletes. There is no `gh`.
  For a release, stage the notes and hand the user `python scripts/publish_release.py`.
  Don't create scratch branches you cannot clean up, unless the user agrees first and
  you give them the branch name to delete (the review-only draft in `triage-pr-review`).
- ⚠️ **The clone is SHALLOW, and `git merge-base` then returns an EMPTY STRING, not an
  error.** A diff against upstream or a tag-anchored range then gives a plausible wrong
  answer. Run `git rev-parse --is-shallow-repository` first;
  `git fetch origin --unshallow --no-recurse-submodules` fixes it.
- ⚠️ **The checkout can be BEHIND what this session pushed, or be reset when the
  container is reclaimed.** Nothing reports it. Before concluding that work is missing,
  or that a review finding does not reproduce: `git log --oneline -1`, then
  `git fetch origin <branch> && git log --oneline HEAD..FETCH_HEAD`. Work you remember
  doing that left no trace is a checkout problem first and a code problem second.
- ⚠️ **A transient 500 is not a capability limit.** `merge_pull_request` returned
  500 with an empty body four times in one session while every read worked, and the
  identical call succeeded first try two days later. The 403s above are the real limits
  and they name themselves. Retry in a later turn before telling the user this session
  type cannot do something.
- ⚠️ **An `add_repo` clone fetches ONLY the default branch, so `git push -u` leaves
  `@{u}` unresolvable and a pushed branch reads as unpushed.** The clone sets
  `remote.origin.fetch` to `+refs/heads/main:refs/remotes/origin/main` alone, so the push
  writes the tracking config with no `refs/remotes/origin/<branch>` to point at. `git
  status` then says "no upstream", `git rev-list @{u}..HEAD` fails, and a stop hook
  reports "1 unpushed commit and no remote branch" on a branch that is already on the
  remote. Confirm with `git ls-remote origin refs/heads/<branch>` against `git rev-parse
  HEAD` before believing it, then add a mapping for THAT branch and fetch it:
  `git config --add remote.origin.fetch
  '+refs/heads/<branch>:refs/remotes/origin/<branch>'` and
  `git fetch origin <branch>`. ⚠️ **`--add`, not a plain set**, which exits 5 with
  "cannot overwrite multiple values with a single value" once the key holds more than
  one refspec (measured). ⚠️ **Not a `*` wildcard either**: it makes every later
  `git fetch` and the documented `--unshallow` pull every branch, and qmk_firmware
  has over 500 `claude/*` branches.
- ⚠️ **`merge_pull_request`'s `expectedHeadSha` must be the full 40 characters.**
  A sha rebuilt from an 8-character prefix returns `409 Head branch was modified` and
  merges nothing; a wrong length returns "The sha parameter must be exactly 40
  characters". Read `.head.sha` from `pull_request_read` for each merge rather than
  reusing a short sha from a commit listing.
- **Chromium is installed headless** (`/opt/pw-browsers/chromium`, also through
  Playwright). Look at generated HTML, SVG and rendered pages instead of reasoning
  about the markup.
- **`gh api` works for reads** through the proxy, although the session says there is
  no `gh`. A wait for a check run or a review is a bash `until` loop over
  `gh api repos/<owner>/<repo>/commits/<sha>/check-runs` with a timeout, which is how
  a push can wait for CodeRabbit's one included review per hour to finish instead
  of cancelling it (2026-10-20). Re-running one job works:
  `gh api -X POST repos/<owner>/<repo>/actions/jobs/<job-id>/rerun` (the HIL job on
  qmk#404 after its ctnd test merged, 2026-10-24). Writes for a release or a tag stay
  untested.
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

Detail and the incidents behind these: [`docs/web-session.md`](web-session.md).
