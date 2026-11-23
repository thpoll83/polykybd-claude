#!/usr/bin/env python3
"""Check that a code move lost no line.

Usage: check_moved_lines.py <base-ref> <source-file> <new-file> [<new-file> ...]

Every non-blank line removed from <source-file> between <base-ref> and the working
tree must appear (whitespace-stripped) in one of the <new-file>s. A dropped leading
`static ` is allowed, in a new file or in <source-file> itself (a function that stays
but becomes shared). Prints the lines it cannot find and exits 1 if there are any.
Run it from the repository root.
"""
import subprocess, sys

def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    base, src, news = sys.argv[1], sys.argv[2], sys.argv[3:]
    diff = subprocess.run(["git", "diff", "-U0", base, "--", src],
                          capture_output=True, text=True, check=True).stdout
    removed = [l[1:].strip() for l in diff.splitlines()
               if l.startswith("-") and not l.startswith("---") and l[1:].strip()]
    pool = set()
    for f in news:
        for l in open(f, encoding="utf-8", errors="replace"):
            l = l.strip()
            if l:
                pool.add(l)
    src_now = {l.strip() for l in open(src, encoding="utf-8", errors="replace") if l.strip()}
    missing = []
    for l in removed:
        if l in pool:
            continue
        if l.startswith("static ") and (l[len("static "):] in pool or l[len("static "):] in src_now):
            continue
        missing.append(l)
    print(f"{len(removed)} removed non-blank lines, {len(missing)} not found in the new file(s)")
    for l in missing:
        print("  MISSING:", l)
    sys.exit(1 if missing else 0)

if __name__ == "__main__":
    main()
