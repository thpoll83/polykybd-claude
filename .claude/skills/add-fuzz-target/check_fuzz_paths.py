#!/usr/bin/env python3
"""Check .github/workflows/polykybd-fuzz.yml against keyboards/polykybd/dev/fuzz/Makefile.

Run from the qmk_firmware root. Exit 0 when:
  - every fuzzed source and header (Makefile SRC + HDRS, i.e. clang -MM) is covered by
    a pull_request `paths:` entry (exact path or a `dir/**` pattern),
  - every `paths:` entry matches at least one file,
  - the job matrix list and the workflow_dispatch target options equal TARGETS.
"""
import glob, os, re, subprocess, sys
import yaml

FUZZ = "keyboards/polykybd/dev/fuzz"
WF = ".github/workflows/polykybd-fuzz.yml"


def make_vars():
    out = subprocess.run(["make", "-C", FUZZ, "-pn", "CC=" + os.environ.get("CC", "clang-18")],
                         capture_output=True, text=True).stdout
    vals = {}
    for line in out.splitlines():
        m = re.match(r"^(SRC|HDRS|TARGETS) :?= (.*)$", line)
        if m:
            vals[m.group(1)] = m.group(2).split()
    return vals


def repo_rel(p):
    return os.path.normpath(os.path.join(FUZZ, p))


def main():
    v = make_vars()
    if not v.get("SRC") or not v.get("HDRS") or not v.get("TARGETS"):
        sys.exit("could not read SRC/HDRS/TARGETS from the Makefile (is clang installed?)")
    files = sorted({repo_rel(p) for p in v["SRC"] + v["HDRS"]})
    wf = yaml.safe_load(open(WF))
    on = wf.get(True) or wf.get("on")
    paths = on["pull_request"]["paths"]
    bad = 0
    for f in files:
        if f.startswith(FUZZ + "/"):
            continue  # the harness dir is covered by its own dir/** entry
        if not any(f == p or (p.endswith("/**") and f.startswith(p[:-2])) for p in paths):
            print("NOT IN paths:", f); bad += 1
    for p in paths:
        if not (glob.glob(p, recursive=True) or os.path.exists(p)):
            print("paths: entry matches nothing:", p); bad += 1
    targets = v["TARGETS"]
    mat = wf["jobs"]["fuzz"]["strategy"]["matrix"]["target"]
    m = re.findall(r'"([a-z_]+)"', mat if isinstance(mat, str) else str(mat))
    if sorted(m) != sorted(targets):
        print("matrix list != TARGETS:", m, targets); bad += 1
    opts = on["workflow_dispatch"]["inputs"]["target"]["options"]
    if sorted(o for o in opts if o != "all") != sorted(targets):
        print("dispatch options != TARGETS:", opts, targets); bad += 1
    print(f"{len(files)} fuzzed files, {len(paths)} paths entries, {len(targets)} targets: "
          + ("OK" if not bad else f"{bad} problem(s)"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
