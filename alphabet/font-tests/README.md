# Font tests

What the font test page
(https://johnservil.github.io/sigil-candidates/check.html) found on each
device that ran it: the measurements behind R7 in
[REQUIREMENTS.md](../../REQUIREMENTS.md).

- `results/N.md` is issue N of
  [johnservil/sigil-candidates](https://github.com/johnservil/sigil-candidates/issues),
  as its sender wrote it, below a header: the issue's link, author, time,
  title, and the page it ran on.
- `pages/COMMIT.html` is that page: sigil-candidates' `check.html` at the
  commit named, the latest before the issue opened. It holds the letters it
  tested and the code that tested them.

`tools/import-fonts.py N` records issue N. `alphabet/alphabet.py` checks
every result against its page and reads which letters each device drew. Its
`MISMEASURED` names the pages whose results it sets aside, and why.
