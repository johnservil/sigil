"""Record font results from sigil-candidates' issues in alphabet/font-tests.

    python3 tools/import-fonts.py N...

Issue N of johnservil/sigil-candidates is a result the font test page sent
(https://johnservil.github.io/sigil-candidates/check.html, made by
tools/check_page.py). It goes to alphabet/font-tests/results/N.md verbatim
(line ends as \\n), below a header: its link, author, time, title, and the
page it ran on, sigil-candidates' latest commit of check.html before the
issue opened, whose check.html goes to alphabet/font-tests/pages/COMMIT.html.
alphabet/alphabet.py reads both. The import checks the result against its
page as alphabet.py does, and stops, naming the issue, at a result already
recorded or one its page could not have sent.
"""

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "alphabet"))
import alphabet

REPO = "johnservil/sigil-candidates"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main():
    numbers = [int(a) for a in sys.argv[1:]]
    assert numbers, __doc__
    for n in numbers:
        out = alphabet.TESTS / "results" / f"{n}.md"
        assert not out.exists(), f"result {n} is recorded already"
        issue = json.loads(get(f"https://api.github.com/repos/{REPO}/issues/{n}"))
        commits = json.loads(get(f"https://api.github.com/repos/{REPO}/commits?path=check.html&until={issue['created_at']}&per_page=1"))
        commit = commits[0]["sha"]
        page = get(f"https://raw.githubusercontent.com/{REPO}/{commit}/check.html")
        kept = alphabet.TESTS / "pages" / f"{commit}.html"
        if kept.exists():
            assert kept.read_bytes() == page, f"{kept.name} is not sigil-candidates' check.html at {commit}"
        else:
            kept.write_bytes(page)
        text = (f"issue: {issue['html_url']}\nauthor: {issue['user']['login']}\ncreated: {issue['created_at']}\n"
                f"title: {issue['title']}\npage: {commit}\n\n" + issue["body"].replace("\r\n", "\n").rstrip("\n") + "\n")
        r = alphabet.font_result(n, text)
        out.write_text(text, encoding="utf-8")
        note = ", set aside: its page mismeasured (alphabet.MISMEASURED)" if commit in alphabet.MISMEASURED else ""
        print(f"result {n}: {r['system']}, {len(r['missing'])} of {len(r['tested'])} letters missing, page {commit[:8]}{note}")


main()
