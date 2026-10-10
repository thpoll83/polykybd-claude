# Code review conventions — the long form

Extracted from `CLAUDE.md` 2026-09-14. The prose is unchanged; only heading levels
and relative links were adjusted to suit a standalone file.

## Code review conventions (all PolyKybd repos)

- **Docstring coverage: ignore CodeRabbit's "Docstring Coverage … threshold 80%" pre-merge check.** That 80% target is a CodeRabbit default, **not** a project policy — the check is non-blocking and we deliberately do not chase it. Do **not** add docstrings to existing functions just to satisfy it (out-of-scope churn). Document new code where a docstring genuinely helps a reader, and no more.

- **Verify an AI reviewer's finding against the code before acting on it — several
  arrive confidently wrong.** Of 7 CodeRabbit findings on one PR (2026-08-01), 3
  were false and **two were refuted by their own evidence**: a "PACK_VERSION 3
  needs a matching host change" (the host never parses the PlyX version — it
  checks magic + slot fit and defers the ABI/RAM contract to the firmware loader
  by design); a "the unpacker is not defined" whose own analysis script had
  returned 159 bytes of output, i.e. it reasoned without the code (the decoder
  was 90 lines above in the same file); and an `int8_t` "signed-overflow UB" that
  the StackOverflow answer it quoted explicitly contradicts (a sub-`int` operand
  promotes to `int`, so the narrowing back is *implementation-defined*, not UB —
  though a real non-termination hazard did lurk nearby, so the fix was taken for
  a different stated reason). **The rule is verify, not dismiss:** the same review
  round produced one genuinely valuable finding (a bulk repair loop running inline
  in `raw_hid_receive()`, worth seconds of blocked main loop) that was adopted.
  Reply to the false ones with the evidence so they are not re-raised.

- ⚠️ **A security-scanner finding on a file under `.github/` or `lib/` is
  probably UPSTREAM's, and two checks settle it in minutes: is it stock, and is it
  reachable?** This is a fork of a 30k-commit project, so almost everything a
  path-based scanner walks was written by someone else and most of it is
  unreachable here. The checks, in order:
  1. **Is it stock?** `diff` the same path against upstream. Byte-identical means
     the finding is upstream's to fix (or not) and ours only if we can reach it:
     ```bash
     curl -sSL "https://raw.githubusercontent.com/qmk/qmk_firmware/master/<path>" \
       | diff - "<path>" && echo "IDENTICAL TO UPSTREAM"
     ```
     ⚠️ **That compares against upstream's CURRENT master, which moves — so read
     the two outcomes asymmetrically.** Identical is conclusive: we did not write
     it. A **difference is not proof we own it** — upstream may simply have
     changed the file since our last catch-up merge. Check
     `keyboards/polykybd/UPSTREAM_PATCHES.md` (the maintained list of upstream
     files we patch) and `git log --oneline -- <path>` before concluding we wrote
     it; getting this backwards means "fixing" an inherited file and buying a
     conflict at the next merge. When the distinction actually decides a finding,
     compare at the **merge base** instead:
     ```bash
     git remote add upstream https://github.com/qmk/qmk_firmware   # usually absent here
     git fetch -q upstream master
     git show "$(git merge-base HEAD upstream/master):<path>" | diff - "<path>"
     ```
     ⚠️ **Run the `--is-shallow-repository` check first** — the container clone is
     shallow, `git merge-base` then returns an **empty string** rather than
     failing, and the command above silently degrades to `git show :<path>`. That
     trap is written up under "Building & flashing"; it is why `master` is the
     default recipe here and the merge base the deliberate escalation.
     ⚠️ **For workflows, don't guess which are ours — ask upstream.** A 404 means
     the file does not exist there, i.e. we wrote it. (This one asks about
     *existence*, not content, so the moving-master caveat above does not apply —
     upstream deleting a workflow we still carry is the only way it misleads.)
     Measured 2026-08-29:
     **only 5 of 23 are ours** — `bump-version.yml`, `cppcheck.yml`,
     `polykybd-unit-test.yml`, `qmk-test.yml`, `release.yml`. Re-derive rather
     than trusting that list:
     ```bash
     for f in .github/workflows/*.yml; do b=$(basename "$f")
       c=$(curl -sSL -o /dev/null -w '%{http_code}' \
           "https://raw.githubusercontent.com/qmk/qmk_firmware/master/.github/workflows/$b")
       [ "$c" = 404 ] && echo "OURS: $b"; done
     ```
  2. **Is it reachable?** For a workflow, read its triggers and its callers — a
     `workflow_call`-only file is dead unless something calls it, and upstream
     gates several on `if: github.repository == 'qmk/qmk_firmware'`, which is
     **permanently false** in a fork. For C, grep the `SRC`/`OBJ` lists: a file no
     build includes cannot have a vulnerability in the shipped image.
  Worked example (2026-08-29): an external audit reported a **critical** template
  injection in `.github/workflows/ci_build_major_branch_keymap.yml`
  (`qmk find -km ${{ inputs.keymap }}`). It is byte-identical to upstream, is
  `workflow_call`-only, and its sole caller is repo-gated — so the chain cannot
  execute here at all. Two commands, no change, finding closed.
  - ⚠️ **The inverse is the part that makes this worth doing: the scanner looked
    at the inherited file and NOT at ours.** The one genuine injection in the same
    sweep was in `bump-version.yml` — a file we wrote — interpolating
    `github.event.pull_request.labels.*.name` straight into a `run:` body, where a
    PR label is attacker-controllable text. Nothing flagged it. **So when a report
    names an upstream path, treat it as a prompt to audit the sibling files we own,
    not just to dismiss the one it named.** The fix pattern is to pass every
    `${{ }}` through `env:` and read it as `"$VAR"` / `os.environ[...]`, which is
    what `bump-version.yml` now does.
    - ⚠️ **That property holds for `bump-version.yml` ALONE — do not read it as
      repo-wide.** A sweep the same day found **31 interpolations inside `run:`
      bodies across 8 workflows**, `qmk-test.yml` and `release.yml` among them.
      None is known to be exploitable — they carry build outputs, `env:` constants
      and `matrix.*` values the workflow itself wrote, not user text — but that is
      a judgement per site, not an audited fact, and the two files have not been
      gone through line by line. `polykybd-claude/.claude/skills/verify-security-finding/`
      carries the checker and the triage procedure.
  - **Record the disposition even when nothing changes** — dismissed findings that
    leave no artifact get re-raised in full by the next scan. The tracker is
    `polykybd-ctnd/docs/SECURITY_AUDIT.md` § *"Checked and NOT vulnerable — don't
    re-litigate"*. For a vendored tree the note belongs beside the code instead:
    `keyboards/polykybd/doom/engine/PROVENANCE.md` carries the disposition of the
    `textscreen/` findings, because that tree is a **verbatim upstream snapshot**
    and must not be patched in place.
  - ⚠️ **A THIRD direction, and it is the one that silences review rather than
    misdirecting it: an inherited upstream POLICY file tells a reviewer to REFUSE
    the files this fork owns.** `.github/copilot-instructions.md` is byte-identical
    to upstream's and says *"This review applies only to changes within the
    `keyboards/` folder … defer to a QMK Collaborator"*. That is written for
    somebody submitting a keyboard to `qmk/qmk_firmware`, where a contributor
    cannot self-approve core changes. Here it means CodeRabbit reads the inherited
    tree normally and declines to assess `release.yml`, `qmk-test.yml` and
    `CLAUDE.md` — **exactly the files that are ours** — deferring them to a role
    this repository has nobody to fill. Measured on #282 (2026-09-09): two findings,
    both "defer to a QMK Collaborator", neither about the code.
    - **The two commands that settle it** are the ones already above, read in the
      opposite direction: `diff` against upstream says the *policy* is inherited,
      and a **404** says the *flagged file* is not.
      ```bash
      curl -sSL "https://raw.githubusercontent.com/qmk/qmk_firmware/master/.github/copilot-instructions.md" \
        | diff - .github/copilot-instructions.md && echo "POLICY IS UPSTREAM'S"
      curl -sSL -o /dev/null -w '%{http_code}\n' \
        "https://raw.githubusercontent.com/qmk/qmk_firmware/master/.github/workflows/release.yml"   # 404 = OURS
      ```
    - ✅ **Reply with that evidence — CodeRabbit withdrew both and stored a repo
      learning**, the general form of which is *"verify whether an instruction
      applies to the fork and the changed file before using it as review scope"*.
      One reply, a permanent correction, same payoff as the stale-netlist reply
      recorded in `PolyKybdHost/CLAUDE.md`. Declining silently buys nothing and the
      finding returns on the next PR that touches `.github/`.
    - ⚠️ **Do not "fix" it by deleting the inherited file.** It is stock upstream,
      so removing it buys a conflict at the next catch-up merge for a problem one
      reply solves. If it becomes tiresome, the place to scope CodeRabbit is its
      own configuration, not upstream's file.

- ⚠️ **A green board is NOT evidence a reviewer read your code, and every bot here
  has a way of going quiet that looks like a clean pass.** The standing check, in
  full, is `pull_request_read` `get_reviews` plus the summary comment's body:
  - a review counts only when its **`commit_id` equals the PR head sha** AND its
    **body is not a refusal notice** (a quota / diff-too-large refusal is a real
    review object carrying the head sha, so the sha alone reads as reviewed);
  - **and the absence of a review object proves nothing either** — a CLEAN
    CodeRabbit pass creates none, it edits its summary comment to say *"No
    actionable comments were generated"*. So read the summary body's `📥 Commits`
    range alongside `get_reviews`.
  - **No check run answers this question.** A green `Sourcery review` /
    `Greptile Review` / CodeRabbit status has accompanied a PR that nothing read,
    measured, more than once.
  - ⚠️ **A check run's CONCLUSION can say `success` while its TITLE reports an
    open alert.** On #255 `CodeQL` read `completed / success / "1 new alert"`
    with an error-severity finding outstanding; a rollup that reads only the
    conclusion calls that commit green. **The alert count is in the title —
    read it, not the conclusion.**
  - ⚠️ **A STACKED PR gets no CodeQL at all.** `codeql.yml` runs only on
    `pull_request: branches: [main]`, so a PR based on another PR's branch shows
    no CodeQL check for as long as it is stacked — and with the other bots
    refusing, it can look finished having been read by nothing. #301
    (2026-10-01) carried no CodeQL check while stacked; ten alerts, one of them
    error severity and failing the check, arrived minutes after it was
    retargeted to `main`. Treat the retarget as the start of review, not the end.
  - ⚠️ **A CodeRabbit "✅ Confirmed as addressed" reply is a review OBJECT
    carrying the head sha — and is NOT a review of that commit.** When it accepts
    your fix on a thread it posts a `COMMENTED` review pinned to the new head, so
    `get_reviews` shows a fresh row with `commit_id == head`, passing the sha test
    above. It has read the THREAD, not the diff. On #257 that row (16:28 on
    `80eeaf6`) sat there while the commit went unreviewed; asking for the review
    explicitly, an hour later, produced a **Major** finding in the very fix it had
    just confirmed. **A thread-level confirmation never substitutes for a review of
    the commit** — check the summary comment's `📥 Commits` range, which still
    named the PREVIOUS head.
  - ⚠️ **Sourcery stops reviewing mid-PR** with `conclusion: skipped`,
    `"⏭️ Auto re-review limit reached"`, after enough pushes. It is an honest
    state and easy to miss in a list of green rows: from that point every
    further push is unreviewed by it. On a long PR, expect to lose Sourcery
    partway and ask CodeRabbit by hand for the pushes that matter.
  - ⚠️ **CodeRabbit gives ONE included review per hour, and a push mid-review
    ABORTS it.** Every summary says *"1 included review per hour; 0 remain after
    this review"*. ⚠️ **A request over the limit is REFUSED, not queued**: three
    `@coderabbitai review` requests posted together (host#327, host#328, qmk#370,
    2026-10-09) each came back *"⚠️ Action not completed — Review rate limited"*, all
    naming the same *"next review in 18 minutes"*, so the hour is shared across the
    repos. Nothing re-runs a refused request. Re-send it after the hour, one PR per
    hour, the PR that merges first first. A push
    while a review is running ends it with *"⚠️ Action not completed — Head commit
    changed"*: no findings, no error, and nothing re-runs it. Push a fix after the
    review lands, or send a fresh `@coderabbitai review` right after the push
    (qmk#319, 2026-09-30).
  - ⚠️ **By 2026-10-08 CodeRabbit auto-review was OFF on all four repos, not only
    `polykybd-docs`.** On qmk#359, host#322 and ctnd#110 it posted *"Review skipped
    — Auto reviews are disabled on this repository"*, and it said the same again on
    every later push. Nothing was reviewed until `@coderabbitai review` was posted
    by hand, once per push that should be read. So **ask for it right after opening
    a PR and after each push that matters**, and treat a PR with no request as
    unreviewed by CodeRabbit, whatever its status rows say. The setting lives in
    the CodeRabbit org UI ("Configuration used: Organization UI"), not in the repo.
  - ⚠️ **`@coderabbitai review` in the PR BODY does nothing; it must be a
    COMMENT.** host#340 (2026-10-09) was opened with the request as the last line
    of its body: CodeRabbit answered *"Review skipped — Auto reviews are
    disabled"* 11 s later, and the review started only when the same text was
    posted as a comment 17 s after that. A body line reads as a request and is
    not one, so post the comment right after `create_pull_request`.
  **The full field guide — which bot goes quiet in which disguise, the sticky
  walkthrough, the Merge Risk sha, the false `✅ Addressed in <sha>` attribution,
  the quota shapes and the rate-limit arithmetic — is the `triage-pr-review`
  skill** in `polykybd-claude`. Load it when you are actually triaging a PR;
  it is ~51 KB that does not belong in every session's context.

- ⚠️ **A review pinned to a MERGE COMMIT reviews the BASE, not your diff — and the
  `commit_id`-vs-head check above does NOT catch it.** That check finds a review of
  an older version of *this branch*; this is a review of somebody else's code that
  reached the branch through a `Merge remote-tracking branch 'origin/main'`. On
  host#248 (2026-09-22) Greptile's header read *"should not merge until
  recovery-copy naming prevents one preserved corrupt settings file from
  overwriting another"* at confidence 4/5, last-reviewed commit `ec2710fc` — a merge
  commit — while `polyhost/settings.py` was **not among the PR's changed files at
  all**. The finding was real code and a real (if narrow) bug; it simply belonged to
  `main` rather than to the PR it was blocking. **Read `pull_request_read`
  `get_files` before acting on a finding**, not the sha alone: a severity label on a
  file your branch never touched is an argument about a different PR.

- ⚠️ **An image is INVISIBLE to the reviewers, so *"that asset is not present in the
  repository"* on a `.png` is structurally false — every time.** CodeRabbit names the
  filter outright in its own comment (`⛔ Files ignored due to path filters (1) …
  is excluded by `!**/*.png``), and Sourcery behaves the same way: on docs#79
  (2026-09-14) it raised the missing-asset finding against
  `tray-menu-forwarder.png` while the commit adding it, `Bin 0 -> 15878 bytes`, sat
  in the same PR and the build emitted its WebP. The reviewer sees a markdown
  reference and no file, and reports the only thing that shape can mean. **Reply
  with the adding commit and that path-filter line**; never "fix" it by re-adding an
  image that is already there.
- **A reviewer's CONCLUSION can be sound while its EVIDENCE is invented — and the
  evidence is worth correcting separately.** The existing rule above says verify and
  decline the false ones. The 2026-08-23 round on PolyKybd#35 sharpened it: **3 of 4
  findings had a defensible conclusion resting on a claim that was simply not true of
  the repo.** (1) *"the netlist shows LED1 uses `WS2812B-Mini`/`C527089`"* — real
  identifiers, read out of a **2024 generated netlist** describing a design two board
  revisions old. (2) *"a later BOM exporter reading `MPN` will produce a wrong
  manufacturer id"* — there **is no `MPN` column** in the BOMs that repo generates; the
  exporter reads `Value`, which was already correct. (3) *"omits the standard footprint
  header"* — it had been added two commits earlier. Only the fourth (an exposed pad
  drawn 5× too tall) was right as stated, and that one was genuinely valuable.
  - **Take the conclusion when it stands on its own merits** — the stale-netlist finding
    led to a real improvement (a library footprint should not restate what the schematic
    instantiates) even though its evidence was junk. Say so explicitly: *"fixed, but for
    a different reason"*.
  - ⚠️ **Reply with the counter-evidence anyway, because CodeRabbit stores a learning
    from the thread.** It did: after being shown the 2024 timestamps and the BOM
    history it recorded *"`*.kicad_sch` files are the authoritative current schematic
    sources… do not use `poly_kb.net`, `poly_kb.xml`… these artifacts are stale"*. That
    is a durable repo-wide fix bought with one reply. Declining silently buys nothing.
  - ⚠️ **The mirror case: a finding can be right about the code and STILL wrong to
    fix, when the code's contract is parity with something else.** Greptile's #200
    finding was correct in every particular — `oled_preview.Renderer.bbox()`
    measures a substituted `'!'` for a missing glyph in a `HINT_SMALL` run while
    `draw()` skips it. Applying the one-line fix would have been wrong anyway: that
    asymmetry is the FIRMWARE's (`kdisp_gfx_text_bbox_in` substitutes with no
    `small` guard; `kdisp_write_gfx_char_half` returns 0), and the module exists to
    mirror the C, not to be internally consistent. "Verify the finding" is not
    enough here — the finding verified fine; what needed checking was whether the
    **remedy** violated a contract the reviewer could not see.
    - **The response that leaves something behind is to pin BOTH halves as a
      test**, with the reasoning in the docstring, so the next reader (or the next
      bot) does not re-raise it — and to say on the thread where the real fix
      belongs. Declining without that just resets the clock.
    - ✅ **And that is what closed it: the real fix landed upstream (qmk#252,
      2026-09-01), so the pin has been INVERTED here.** `Renderer.bbox()` now skips
      an unresolvable glyph in a `HINT_SMALL` run instead of substituting `'!'`,
      matching `kdisp_gfx_text_bbox_in`; the test that pinned the old behaviour is
      `test_small_skips_a_missing_glyph_instead_of_substituting_bang`, ported from
      the C's own new case. **The lesson is unchanged and this is its payoff** —
      declining a correct finding on parity grounds only holds while somebody
      carries it to the end the contract points at. ⚠️ It also means a parity pin
      is a LIABILITY the moment the other side moves: nothing here would have
      failed, so the divergence would simply have flipped direction in silence.
      When you pin one, name the upstream change that would invalidate it.

- **When two reviewers disagree about the same code, WRITE THE TEST — it
  adjudicates, and it is faster than arguing.** On PR #154 (2026-08-07) Sourcery
  asked for a regression test on a parser input shape while CodeRabbit claimed
  that shape silently returned an empty result. Writing the test settled it in
  seconds: CodeRabbit was right, and the docstring had been advertising a shape
  the code dropped. The general form is worth internalising — a "testing
  suggestion" from one reviewer is often the cheapest way to check a
  *correctness* claim from another, and unlike a code-reading argument it leaves
  a permanent guard behind. It also inverts nicely: a test that passes
  immediately is evidence the finding was wrong, which is exactly the evidence
  to paste in the reply.

- **A guard that ENUMERATES its siblings will go stale — delete it rather than
  add the missing term, and distrust a test that documents the workaround.**
  `find_matching_entry` (`handler/common.py`) split the window title only
  `if title and (has_starts_with or has_ends_with)`, while the *third* word-based
  matcher below it, `has_contains`, was never added to that list. So
  `titles-contains` could not match unless the entry happened to declare a
  sibling key it did not need — and the shipped browser entry's Miro / web-Outlook
  / Jira overlays, which route purely on `titles-contains`, **had never once
  rendered** since they were added (#156, 2026-08-11). Two things to carry over:
  - **The fix is to drop the gate** (`words = title.split() if title else []`),
    not to add `or has_contains`. Every branch under it already checks its own
    `has_*` flag, so the gate's only job was to restate them and stay in sync —
    exactly what it failed at, and one more term re-arms the same trap for
    whoever adds a fourth matcher.
  - ⚠️ **The test suite was green throughout, because the test encoded the
    workaround as the contract**: it built its fixture as
    `entry(sw={"x": {}}, contains={...})` with the comment *"has both starts_with
    and contains so the title is split into words"*. That dummy `titles-startswith`
    is the only reason it passed. A fixture carrying an unexplained extra key to
    make the feature under test work is a **bug report**, not setup — chase it.
- **Sourcery's `dangerous-subprocess-use-audit` (opengrep) fires on ANY
  non-literal argv and will hold the check red forever — resolve it with a
  `# nosemgrep` marker plus a written audit, not by contorting the code.** It is
  an *audit* rule: it asks a human to confirm where the argv came from, which is
  the whole remedy. A `subprocess.run(list, ...)` with the default
  `shell=False` has no shell to inject through, and the rule's suggested
  `shlex.quote` escapes for a **shell string** — applied to an argv element it
  just corrupts the value. ⚠️ **The marker only applies to the line IMMEDIATELY
  following it**, so putting it at the top of an explanatory comment block (where
  it reads best) silently does nothing and the check stays red — cost an extra
  push on #154. Record the reasoning above the block, the marker directly above
  the call. Leaving the check red instead is the worse option: an always-red
  check is one people learn to scroll past, and the next real finding rides in
  behind it.


- ⚠️ **After changing a function SIGNATURE, grep THIS FILE for other prose
  references to it — nothing in CI reads Markdown, so a stale API example ships
  silently.** `CLAUDE.md` narrates dozens of APIs across sections that have no
  reason to be open when you edit one, and an example that no longer compiles is
  worse than no example: it reads as authoritative and the next session copies it.
  Changing `kdisp_set_gfx_scanline(bool)` to `(bool, uint8_t)` updated the section
  being edited and left the one-arg form in two *other* notes — the `kdisp_plot_ink`
  account of the EDEN dimming bug and the Eden-screensaver section (#267,
  2026-09-02). Every build was green under `-Werror` precisely because the **code**
  call sites were all correct. The check is one command, before you push:
  ```bash
  grep -n "kdisp_set_gfx_scanline" CLAUDE.md    # …and any other renamed symbol
  ```
  - **It was caught by Greptile, and that is the pattern rather than the luck.**
    A cross-file consistency claim in prose is what an LLM reviewer is genuinely
    better at than every other check here — cppcheck cannot read the file, the
    compiler cannot see it, and the author is the one person guaranteed not to
    re-read the sections they did not open. The same reviewer caught a note
    contradicting one two paragraphs above it earlier (`PolyKybdHost/CLAUDE.md`).
    So when a reviewer raises a *documentation* inconsistency, verify it like any
    other finding — but expect it to be right more often than its severity label
    suggests.
  - ⚠️ Applies to a **renamed or re-typed** symbol just as much as a new argument,
    and to the sibling repos' `CLAUDE.md` files when the symbol is one they mirror
    (`iso_lang_country.py`, `noto-fonts.yaml`, the font-pack render manifests).


- **Sourcery's `dangerous-subprocess-use-audit` is a BLOCKING check here too, and it
  wants a marker plus a written audit, not contorted code.** It fires on any
  `subprocess.run(cmd, …)` whose argv is a variable, even a literal list chosen three
  lines above. The firmware repo's Python (`tools/`, `tools/hil_probes/`) hits it the
  same way the host does. Put `# nosemgrep:
  python.lang.security.audit.dangerous-subprocess-use-audit` on the line
  **immediately before** the call, with the audit (where `cmd` comes from, no shell)
  above the marker. A marker placed atop the comment block does nothing. On #341
  (2026-10-07, `usb_reset_race.py:92`) this cleared the failed check in one push:
  Sourcery marked the thread addressed and approved the PR.
