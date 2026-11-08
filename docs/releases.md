# Releases: the rules every PolyKybd repo shares

Moved 2026-10-10 from the Releases sections of `qmk_firmware/CLAUDE.md` and
`PolyKybdHost/CLAUDE.md`, verbatim. The per-repo mechanics stay in each repo:
qmk `keyboards/polykybd/RELEASES.md`, host `docs/releases.md`, wincompose `RELEASE.md`.

## As written in the firmware CLAUDE.md

Firmware releases are **GitHub Releases** (tag `PolyKybd-fw-vX.Y.Z`; `FW_VERSION` in
`config.h`), created by **publishing** — *not* by pushing a tag, which lands on the
auto-bump `[skip ci]` commit and triggers nothing. Use the `polykybd-github-release`
skill; the mechanics, the `release-notes` branch and `scripts/publish_release.py` are in
[`keyboards/polykybd/RELEASES.md`](../../qmk_firmware/keyboards/polykybd/RELEASES.md).

- ⚠️ **`scripts/publish_release.py` is byte-identical across `qmk_firmware`,
  `PolyKybdHost` and `wincompose`, nothing checks that, and it had already
  diverged in BOTH directions at once** — these two repos held the
  commit-pin and the `make_latest` correctness, wincompose held the
  create-time gate, and each copy was the newer one for a different thing.
  `md5sum */scripts/publish_release.py` is the check. Its tests live in
  **`PolyKybdHost/tests/scripts/publish_release_test.py`**, the only one of
  the three repos with a Python runner, so a break introduced here fails
  there.

- ⚠️ **The assets are named from the TAG, and `release.yml` now REFUSES a tag whose
  tree declares a different `FW_VERSION`** — its first step, before the build and before
  the fwapply gate, so a refusal changes nothing. Otherwise a release published before
  its bump merged ships `polykybd_split72_v<tag>.bin` built from a tree declaring
  another number: the board reports one version, the download claims another, and the
  host updater offers that release forever because the install can never reach the
  advertised number. wincompose shipped exactly that (`PK-0.9.19`). ⚠️ **The fix is to
  MOVE the tag, and only while no release holds it** — publishing never moves one, and
  a dispatch would build the dispatch ref and leave the tag on the old tree. Delete the
  assetless release the refusal left behind first. `RELEASES.md` → the asset-naming
  bullet has both refusal cases.

- ⚠️ **Publishing is GATED on a green firmware-APPLY run for the commit being released**
  (`tools/require_fwapply_run.py`). The HID-apply brick shipped because no release
  artifact had ever been applied on hardware — the rig flashes by UF2 over GPIO BOOTSEL,
  which bypasses `fw_staging` entirely. It walks back through ancestors and proves the
  delta to the release commit is **only** the auto-bump. Recovery when it refuses:
  dispatch *Build and HIL Test* on that commit with `tier: fwapply`, then re-run release.
  ⚠️ **A docs-only merge in the way no longer costs that round-trip**: the delta may
  also carry files the build and the rig never read, decided by replaying
  `qmk-test.yml`'s own `paths:` filter rather than a second copy of it, and failing
  closed if that filter cannot be read. `PolyKybd-fw-v0.27.1` published with zero
  assets before this existed. `bump:none` additionally skips the version bump for such
  a PR — a convenience, since the gate no longer depends on anyone remembering it.
  ⚠️ **Publishing within ~11 minutes of a firmware merge RACES that merge's own apply
  run, and the gate only accepts a FINISHED green one.** v1.3.1 was published at ~08:27;
  the #320 merge run's apply job finished at 08:32:37; the gate checked at 08:29 and
  refused (2026-09-30). **On a refusal, first look up the runs for the newest firmware
  merge commit BY `head_sha`** — if its apply job is still running, wait and re-run the
  release; a `tier: fwapply` dispatch is for a merge whose run went red or never started.
  ⚠️ **Never read "no run exists" off a filtered run listing.** `list_workflow_runs`
  filtered by branch + event omitted the three newest merge runs, which produced the
  false claim that squash merges start no HIL run; the `head_sha` query found all three.
- ⚠️ **A `PROTOCOL_VERSION` bump means BOTH artifacts get released, and the check is the
  PUBLISHED versions, not the in-tree ones.** The source-lockstep rule can be perfectly
  satisfied while the releases sit a protocol apart, and nothing downstream catches it —
  the connect gate is not exact-match, so an old host pairs with new firmware and
  silently leaves the new features off. **Publish the host first**, then the firmware.
- ⚠️ **Since 1.0, PATCH is the default and `bump:minor` is the exception** (maintainer's
  rule, 2026-10-03). Before 1.0 a small change landed as a 0.9.x patch; after 1.0 almost
  every PR carried `bump:minor`, so the firmware went 1.0.0 → 1.7.0 in six days and the
  host 1.3.0 → 1.15.0 in nine. Leave the label off (patch) for fixes, diagnostics,
  developer tools and small additions, **even when the PR bumps `PROTOCOL_VERSION`**:
  the protocol is its own number. Use `bump:minor` only for a feature an owner would
  call new, the kind that names a release. When unsure, ask.
- ⚠️ **A MISSING bump label is silent, and "before the merge" means AT OPEN.** The label
  is read at merge time; a request in the PR body is documentation, not a label, and one
  applied as the merge happens lands too late (twice, 12 s late once). `create_pull_request`
  cannot set labels — use `issue_write` with `labels:` right after opening. A missing
  label made the live docs promise a version that would never exist, because a docs PR
  ships the moment it merges while a firmware PR only bumps a number and waits.
  ⚠️ **Then READ THE LABELS BACK a few minutes later** — a successful `issue_write` is
  not proof the label stayed. On qmk#319 (2026-09-30) `bump:minor` was set at 06:53 and
  gone by 07:20, leaving only `keyboard`; the Pull Request Labeler had run on open at
  06:52, most likely writing its list from a snapshot taken before ours (inferred, not
  proven). The host PR, which has no labeler, kept its label. Unnoticed, 1.3.0 would
  have shipped as 1.2.1. Re-set it as the FULL list (`["keyboard","bump:minor"]`) —
  `issue_write` replaces, it does not add.
- ⚠️ **From Claude Code on the web you can neither push tags nor create a release** —
  stage the notes on the branch and hand the user `python scripts/publish_release.py`.


## As written in the host CLAUDE.md

Host releases are **GitHub Releases** (tag `vX.Y.Z`; version in `polyhost/_version.py`),
created by **publishing** — *not* by pushing a tag, which lands on the auto-bump
`[skip ci]` commit and triggers nothing. Use the `polykybd-github-release` skill; the
mechanics, the `release-notes` branch convention and `scripts/publish_release.py` are
in [`docs/releases.md`](../../PolyKybdHost/docs/releases.md).

- ⚠️ **`scripts/publish_release.py` is byte-identical across `qmk_firmware`,
  `PolyKybdHost` and `wincompose`, nothing checks that, and it had already
  diverged in BOTH directions at once** — these two repos held the
  commit-pin and the `make_latest` correctness, wincompose held the
  create-time gate, and each copy was the newer one for a different thing.
  `md5sum */scripts/publish_release.py` is the check. Its tests live in
  **`PolyKybdHost/tests/scripts/publish_release_test.py`**, the only one of
  the three repos with a Python runner, so a break introduced here fails
  there.

- ⚠️ **`release.yml` now REFUSES a tag whose tree declares a different
  `__version__`** — its first step, before the release is created or its notes edited.
  The updater compares exactly those two numbers (`updater.py` fetches
  `archive/refs/tags/<tag>.tar.gz` and tests the installed `__version__` against
  `_version_from_tag(tag)`), so a release published before its bump merged hands out a
  tarball that can never reach the advertised version — and every later check offers
  the same update again, forever. wincompose shipped that failure through its own
  mechanism (`PK-0.9.19`). ⚠️ **It DETECTS rather than PREVENTS here** — this workflow
  uploads nothing, so there is no asset to withhold, and on `release: published` the
  release is public before the step runs; withdrawing it is manual. The pre-publish
  defence is `publish_release.py`. ⚠️ **The fix is to MOVE the tag, and only while no
  release holds it** — publishing never moves one, and the tarball people install IS
  `archive/refs/tags/<tag>.tar.gz`, so delete the release the refusal left behind before
  moving anything. [`docs/releases.md`](../../PolyKybdHost/docs/releases.md) → the first bullet has both
  refusal cases.

- ⚠️ **A `PROTOCOL_VERSION` bump means BOTH artifacts get released, and the check is
  the PUBLISHED versions, not the in-tree ones.** The source-lockstep rule can be
  perfectly satisfied while the releases sit a protocol apart, and nothing downstream
  catches it because the connect gate is not exact-match — an old host pairs with new
  firmware and silently leaves the new features off. **Publish the host first**, then
  the firmware.
- ⚠️ **Version bump is label-driven, and the label must be set AT OPEN.** A request in
  the PR body is documentation, not a label; `bump-version.yml` reads labels at merge
  time and a label applied as the merge happens lands too late. `create_pull_request`
  cannot set labels — use `issue_write` with `labels:` right after opening.
- ⚠️ **The bump lands through its own auto-merged PR, because `main` requires a PR**
  (2026-10-09). It depends on "Allow GitHub Actions to create and approve pull requests"
  and on the `main` rule requiring a PR and nothing more: a required check or approval
  would leave every bump PR hanging. Details in [`docs/releases.md`](../../PolyKybdHost/docs/releases.md).
- ⚠️ **Since 1.0, PATCH is the default and `bump:minor` is the exception** (maintainer's
  rule, 2026-10-03). Before 1.0 a small change landed as a 0.9.x patch; after 1.0 almost
  every PR carried `bump:minor`, so the firmware went 1.0.0 → 1.7.0 in six days and the
  host 1.3.0 → 1.15.0 in nine. Leave the label off (patch) for fixes, diagnostics,
  developer tools and small additions, **even when the PR bumps `PROTOCOL_VERSION`**:
  the protocol is its own number. Use `bump:minor` only for a feature an owner would
  call new, the kind that names a release. When unsure, ask.
- **Host and firmware version numbers are NOT kept in lockstep** (they were aligned
  once, at 0.11.0, cosmetically). The number that must move together is
  `__protocol__` / `PROTOCOL_VERSION`.
- ⚠️ **From Claude Code on the web you can neither push tags nor create a release** —
  stage the notes on the branch and hand the user `python scripts/publish_release.py`.
  The same proxy 403s on branch **deletion**, so don't create scratch branches you
  can't clean up.


## publish_release.py: a lookup is three-valued, and a timeout needs an `except`

Added 2026-11-08 from the release-gate session (qmk#376, host#349, host#354). Not part
of the verbatim archives above.

Three lookups answer in **three** values, and collapsing any of them to two is how the
check stops checking: `release_exists()` returns `True`/`False`/`None`, `tag_commit()`
returns a sha/`""`/`None`, and the host `release.yml` withdrawal step reports
`yes`/`no`/`unknown`. **Only a 404 means "confirmed absent".** A 401, a 403, a 5xx or a
timeout all mean "cannot tell", and the caller must then take the stricter path. Each
of the three was first written with two values and corrected after a review found it
(Revix and Greptile on wincompose#25, Greptile on host#318 and qmk#356).

⚠️ **A 404 from `releases/tags/<tag>` means no PUBLISHED release, which is weaker than
no release.** GitHub documents that endpoint as "Get a published release with the
specified tag", and documents drafts as listed only to callers with push access ("Only
users with push access will receive listings for draft releases", *List releases*). So a
draft carrying that `tag_name` reads as absent there however the call is authenticated.
Before moving a tag on the strength of a 404, list the releases with a push-access
credential and look for a draft. ⚠️ **`--paginate` is required**: a repository with
more than one page of releases can hold the draft on a later page, and the single-page
form reports no draft:

```bash
gh api --paginate "repos/<owner>/<repo>/releases?per_page=100" \
  --jq '.[] | select(.draft) | .tag_name'
```

A failed request here is inconclusive, not evidence that no draft exists, so check the
exit status before acting on an empty result. What status code the by-tag endpoint
returns for a draft-only tag is not documented; treat it as unverified rather than
assuming the 404.

⚠️ **A read timeout only helps if something catches what it raises.** `API_TIMEOUT = 30`
is passed to every `urlopen()` so that a connection GitHub accepts and then stops
answering cannot block forever. `release_exists()` and `_get_json()` each end with
`except Exception: return None`, so a timeout there becomes their "cannot tell" value.
`api()` catches only `urllib.error.HTTPError`, so a timeout raises an uncaught traceback
— on the create path that is *after* the POST has been sent, with no way to tell whether
the release was created. The timeout made that failure louder rather than safer.

⚠️ **The two failure phases raise DIFFERENT types, so `except OSError` is the one
catch that covers both.** Measured on Python 3.11.18:

| phase | what `urlopen()` raises | `URLError`? | `TimeoutError`? | `OSError`? |
|---|---|---|---|---|
| connect | `urllib.error.URLError` wrapping the socket error | yes | no | yes |
| response read | bare `builtins.TimeoutError` | **no** | yes | yes |

`do_open()` wraps an `OSError` from `h.request()` as `URLError`, so every connect-phase
failure arrives as `URLError`; a timeout from `h.getresponse()` is not wrapped and
arrives as `TimeoutError` (since 3.10 `socket.timeout` is an alias of it). So catching
`URLError` alone misses the read timeout, and catching `TimeoutError` alone misses the
connect failure. `except Exception` is what makes the two sibling lookups safe; a fix for
`api()` needs `OSError` or wider.

⚠️ **An earlier version of this note claimed both phases raise a bare `TimeoutError`,
from a test whose server called `accept()` in both branches** — so neither case was a
connect-phase failure. Reproduce the read timeout with:

```python
import socket, threading, time, urllib.request
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
threading.Thread(target=lambda: (srv.accept(), time.sleep(5)), daemon=True).start()
urllib.request.urlopen(f"http://127.0.0.1:{srv.getsockname()[1]}/", timeout=1)
```

Unfixed as of 2026-11-08. The fix must be applied to all three copies in one change,
because nothing in CI compares them (see *Files kept byte-identical across repos*).
