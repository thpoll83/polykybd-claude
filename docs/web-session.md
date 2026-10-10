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
