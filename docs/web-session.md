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
