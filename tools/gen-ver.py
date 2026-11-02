"""Release version and tag: `python3 tools/gen-ver.py X.Y.Z` from a clean tree.

One commit, on top of whatever HEAD is, setting every copy of the version to
X.Y.Z+<HEAD's hash>, and the tag vX.Y.Z+<hash> on it. The hash inside the
version string names the code commit, so whoever holds the string and
nothing else can later check they have the right code (a string cannot hold
the hash of the commit it sits in, so it holds its parent's; the release
commit changes version strings alone). Zooko's scheme, shared with his other
projects (the servil fork's tools/gen-ver.py).

The copies: the Rust crate (rust/Cargo.toml and its lock), the TypeScript
package (typescript/package.json), and the newest heading of CHANGELOG.md,
`## Sigil X.Y...`, which then names the full version.

The rest of a release, after this commit:
1. git push origin HEAD:main vX.Y.Z+<hash>
2. (cd rust && cargo publish)
3. Download the crate back from crates.io, check that `cargo package` at the
   tag gives the same bytes, and record its SHA-256 and BLAKE3 in the GitHub
   release, whose text is the CHANGELOG entry.
"""
import json
import os
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def edit(path, pattern, replacement):
    """Replace the first line matching `pattern`; stop if none does."""
    with open(path, encoding="utf-8") as f:
        text, n = re.subn(pattern, replacement, f.read(), count=1, flags=re.M)
    if n != 1:
        sys.exit(f"{path}: no line matches {pattern}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
    sys.exit("usage: python3 tools/gen-ver.py X.Y.Z")
version = sys.argv[1]
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if git("status", "--porcelain"):
    sys.exit("the tree must be clean")
number = lambda v: tuple(map(int, v.split("+")[0].split(".")))
tags = [number(t[1:]) for t in git("tag", "-l", "v*").split()]
if tags and number(version) <= max(tags):
    sys.exit(f"{version} is not newer than the latest tag, v{'.'.join(map(str, max(tags)))}")

full = f"{version}+{git('rev-parse', 'HEAD')}"
edit("rust/Cargo.toml", r'^version = ".*"$', f'version = "{full}"')
subprocess.run(["cargo", "update", "-q", "-p", "sigilcode"], cwd="rust", check=True)
edit("typescript/package.json", r'^  "version": ".*",$', f'  "version": "{full}",')
assert json.load(open("typescript/package.json"))["version"] == full
edit("CHANGELOG.md", r"^## Sigil [^\s,]+", f"## Sigil {full}")
git("commit", "-q", "-m", f"Version {full}", "--",
    "rust/Cargo.toml", "rust/Cargo.lock", "typescript/package.json", "CHANGELOG.md")
git("tag", f"v{full}")
print(f"v{full}")
# The dependency line for the release notes: the full version, exactly.
print(f'sigilcode = "={full}"')
