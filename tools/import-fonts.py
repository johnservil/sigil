"""Append font results from sigil-candidates' issues to alphabet/fonts.txt.

    python3 tools/import-fonts.py N...

Each issue N is a result the font test page sent (tools/check_page.py,
published as https://johnservil.github.io/sigil-candidates/check.html), in
one fenced block: the browser's user agent, the line naming the page's
candidates by count and fingerprint, and a line a script, "Script:
drawn/all", with "missing" and the code points it drew as boxes, in hex
ranges (a submitter's note beside the block stays in the issue). It becomes
`result N`, dated by the issue and named by system and browser, tested on
alphabet/candidates.txt's letters, and missing what the issue lists. A
result already in the file, a page whose candidates are not
candidates.txt's, counts that do not add up, or a line the page never
writes stops the import, named.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "alphabet" / "fonts.txt"
sys.path.insert(0, str(ROOT / "tools"))
import check_page
ISSUE = "https://api.github.com/repos/johnservil/sigil-candidates/issues/{}"


def expand(ranges):
    """The code points of space-separated hex ranges ("0904-0928 093D")."""
    out = []
    for r in ranges.split():
        a, _, b = r.partition("-")
        out.extend(range(int(a, 16), int(b or a, 16) + 1))
    return out


def ranges(points):
    """Code points as fonts.txt writes them: sorted uppercase hex ranges."""
    points, out = sorted(set(points)), []
    for p in points:
        if out and p == out[-1][1] + 1:
            out[-1][1] = p
        else:
            out.append([p, p])
    return " ".join(f"{a:04X}" if a == b else f"{a:04X}-{b:04X}" for a, b in out)


def name(ua):
    """System and browser, as fonts.txt names them ("Android Chrome")."""
    system = next(s for pattern, s in [(r"iPhone|iPad", "iOS"), (r"Android", "Android"), (r"Macintosh", "macOS"),
                                       (r"Windows", "Windows"), (r"CrOS", "ChromeOS"), (r"Linux", "Linux"), (r"", "Other")]
                  if re.search(pattern, ua))
    browser = next(b for pattern, b in [(r"Brave", "Brave"), (r"Firefox/|FxiOS", "Firefox"), (r"Edg", "Edge"), (r"; wv\)", "WebView"),
                                        (r"Chrome/|CriOS", "Chrome"), (r"Safari/", "Safari"), (r"", "browser")]
                   if re.search(pattern, ua))
    return f"{system} {browser}"


def result(n, issue, page):
    """fonts.txt's lines for issue n, sent by the page whose candidates are
    `page` (candidates.txt's text)."""
    # The page's result is the issue's fenced block; a note around it stays in the issue.
    block = re.search(r"```\n(.*?)\n```", issue["body"], re.S)
    assert block, f"issue {n}: no result block"
    lines = [l for l in block[1].splitlines() if l.strip()]
    ua, missing, total = lines[0], [], 0
    tested = [c for v in check_page.candidates(page).values() for c in v]
    want = f"Sigil font test {check_page.ROUND}: {len(tested)} candidates, set {check_page.fingerprint(page)}"
    assert lines[1] == want, f"issue {n}: {lines[1]!r}, where candidates.txt is {want!r}"
    for line in lines[2:]:
        if line.startswith("Drawn in full:"):
            continue
        m = re.fullmatch(r"([A-Za-z_]+): (\d+)/(\d+)(?: missing ([0-9a-f -]+))?", line)
        assert m, f"issue {n}: a line the page never writes: {line!r}"
        drawn, count = int(m[2]), int(m[3])
        gone = expand(m[4] or "")
        assert drawn + len(gone) == count, f"issue {n}: {m[1]} counts {drawn} + {len(gone)} missing of {count}"
        missing += gone
        total += count
    assert total == len(tested), f"issue {n}: {total} characters, where the page tests {len(tested)}"
    assert set(missing) <= set(tested), f"issue {n}: a missing character the page does not test"
    return (f"result {n} {issue['created_at'][:10]} {name(ua)}\nua {ua}\ntested {ranges(tested)}\n"
            f"missing {ranges(missing)}\n")


def main():
    numbers = [int(a) for a in sys.argv[1:]]
    assert numbers, __doc__
    text = FONTS.read_text()
    have = [int(n) for n in re.findall(r"^result (\d+) ", text, re.M)]
    page = (ROOT / "alphabet" / "candidates.txt").read_text(encoding="utf-8")
    for n in numbers:
        assert n not in have, f"result {n} is in fonts.txt already"
        with urllib.request.urlopen(ISSUE.format(n)) as r:
            text = text.rstrip("\n") + "\n\n" + result(n, json.load(r), page)
        have.append(n)
    FONTS.write_text(text)


main()
