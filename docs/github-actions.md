# GitHub Actions versions in our workflows

## The Node 24 move (2026-11-07)

GitHub runs actions built for Node 20 on Node 24 and warns on every run ("Node.js 20
is deprecated. The following actions target Node.js 20 but are being forced to run
on Node.js 24"). Such an action keeps running only as long as its code works on
Node 24, and the warning stays until we move to a major built for Node 24. The first
major of each action whose `action.yml` says `using: node24`:

| action | first Node 24 major | used in our workflows |
|---|---|---|
| `actions/checkout` | v5 | v6, and v5 in both `bump-version.yml` |
| `actions/upload-artifact` | v6 (v5 still defaults to Node 20) | v6 |
| `actions/download-artifact` | v7 (v5 and v6 still default to Node 20) | v7 |
| `actions/github-script` | v8 | v8 |
| `actions/setup-python` | v6 | v6 |

Check a version yourself rather than trusting a changelog:
`curl -s https://raw.githubusercontent.com/actions/<name>/<tag>/action.yml | grep using:`.

- **The Node 24 majors need Actions runner 2.327.1 or newer.** The HIL rig is a
  self-hosted runner. Its version is the "Current runner version" line at the top
  of any HIL job log (2.338.2 on 2026-11-07).
- **download-artifact v5 changed where a download BY ID is extracted** (now `path/`,
  as for a download by name). Every download in our workflows goes by `name:`, so it
  does not apply. Check this again before adding an `artifact-ids:` download.
- **Both `bump-version.yml` stay on checkout v5, not v6.** v6 stores the push
  credentials in a separate file that git loads through `includeIf`. The bump push
  runs only when a PR merges, so a change there cannot be tested beforehand; v5 runs
  on Node 24 and keeps the old credential storage. The host's v5 bump pushed 1.19.63
  on 2026-11-07. The firmware's had not run yet, because its PR (qmk#415) carried
  `bump:none`.
- Upstream QMK's workflows in `qmk_firmware` are left as they are.

PRs: thpoll83/qmk_firmware#415, thpoll83/PolyKybdHost#702, thpoll83/polykybd-ctnd#137.
