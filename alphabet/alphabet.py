"""Sigil's alphabet, computed from Unicode's data files and the font tests in
font-tests/ by the steps of REQUIREMENTS.md's "The alphabet": the whole
computation, in one script with no dependencies beyond Python 3.

    python3 alphabet/alphabet.py [--data DIR] [--check]

It downloads the data files of every Unicode release from 6.0.0 to 18.0.0
from unicode.org (or reads them from DIR, and saves there what it
downloads), checks each by SHA-256 and by BLAKE3 (below, in plain Python;
unicode-files.txt lists both) before reading it, checks each font result
against the page that measured it, and writes alphabet.txt,
skipped.txt, typescript/alphabet.ts and lean/Sigil/Alphabet.lean; with
--check it confirms that those files are its output. Every property comes
from the data files, none from Python's own tables, so the same files give
the same alphabet with any Python on any machine. Each step names the
constraint (R) or desideratum (D) of REQUIREMENTS.md it serves.
"""
import collections
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.unicode.org/Public/"

# R12: the releases whose data every letter's record covers, oldest first;
# the newest also gives the letters' ages (D9) and the look-alikes (R8, D4).
RELEASES = ["6.0.0", "6.1.0", "6.2.0", "6.3.0", "7.0.0", "8.0.0", "9.0.0", "10.0.0", "11.0.0", "12.0.0",
            "12.1.0", "13.0.0", "14.0.0", "15.0.0", "15.1.0", "16.0.0", "17.0.0", "18.0.0"]
NEWEST = RELEASES[-1]
UCD = ["UnicodeData.txt", "Scripts.txt", "PropList.txt", "DerivedCoreProperties.txt",
       "DerivedNormalizationProps.txt", "ArabicShaping.txt", "LineBreak.txt", "auxiliary/WordBreakProperty.txt",
       "EastAsianWidth.txt"]


# BLAKE3 (unkeyed), from the specification (github.com/BLAKE3-team/BLAKE3-specs),
# for checking each data file's second hash with nothing outside this script.
# It checks itself against BLAKE3's published hash of the empty input.

IV = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8]
CHUNK_START, CHUNK_END, PARENT, ROOT_FLAG = 1, 2, 4, 8
M32 = 0xFFFFFFFF


def g(s, a, b, c, d, x, y):
    s[a] = (s[a] + s[b] + x) & M32
    s[d] ^= s[a]
    s[d] = (s[d] >> 16 | s[d] << 16) & M32
    s[c] = (s[c] + s[d]) & M32
    s[b] ^= s[c]
    s[b] = (s[b] >> 12 | s[b] << 20) & M32
    s[a] = (s[a] + s[b] + y) & M32
    s[d] ^= s[a]
    s[d] = (s[d] >> 8 | s[d] << 24) & M32
    s[c] = (s[c] + s[d]) & M32
    s[b] ^= s[c]
    s[b] = (s[b] >> 7 | s[b] << 25) & M32


def compress(cv, m, counter, block_len, flags):
    s = cv[:8] + IV[:4] + [counter & M32, counter >> 32 & M32, block_len, flags]
    for r in range(7):
        g(s, 0, 4, 8, 12, m[0], m[1]); g(s, 1, 5, 9, 13, m[2], m[3])
        g(s, 2, 6, 10, 14, m[4], m[5]); g(s, 3, 7, 11, 15, m[6], m[7])
        g(s, 0, 5, 10, 15, m[8], m[9]); g(s, 1, 6, 11, 12, m[10], m[11])
        g(s, 2, 7, 8, 13, m[12], m[13]); g(s, 3, 4, 9, 14, m[14], m[15])
        if r < 6:
            m = [m[i] for i in PERMUTATION]
    return [s[i] ^ s[i + 8] for i in range(8)] + [s[i + 8] ^ cv[i] for i in range(8)]


def words(block):
    block = block + bytes(64 - len(block))
    return [int.from_bytes(block[4 * i:4 * i + 4], "little") for i in range(16)]


def chunk_output(chunk, counter):
    """(cv, block words, counter, block length, flags) of a chunk's last block."""
    cv = IV
    blocks = [chunk[i:i + 64] for i in range(0, len(chunk), 64)] or [b""]
    for i, block in enumerate(blocks):
        flags = (CHUNK_START if i == 0 else 0) | (CHUNK_END if i == len(blocks) - 1 else 0)
        if i == len(blocks) - 1:
            return cv, words(block), counter, len(block), flags
        cv = compress(cv, words(block), counter, 64, flags)[:8]


def chaining_value(out):
    cv, m, counter, block_len, flags = out
    return compress(cv, m, counter, block_len, flags)[:8]


def blake3(data):
    """BLAKE3's 32-byte hash of `data`."""
    chunks = [data[i:i + 1024] for i in range(0, len(data), 1024)] or [b""]
    stack = []
    for i, chunk in enumerate(chunks[:-1]):
        cv, total = chaining_value(chunk_output(chunk, i)), i + 1
        while total & 1 == 0:
            cv = chaining_value((IV, stack.pop() + cv, 0, 64, PARENT))
            total >>= 1
        stack.append(cv)
    out = chunk_output(chunks[-1], len(chunks) - 1)
    while stack:
        out = (IV, stack.pop() + chaining_value(out), 0, 64, PARENT)
    cv, m, _, block_len, flags = out
    return b"".join(w.to_bytes(4, "little") for w in compress(cv, m, 0, block_len, flags | ROOT_FLAG)[:8])


assert blake3(b"").hex() == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262", "this BLAKE3 is wrong"


def pinned():
    """unicode-files.txt: {path under BASE: (SHA-256, BLAKE3)}."""
    out = {}
    for line in (ROOT / "alphabet" / "unicode-files.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            path, sha, b3 = line.split()
            out[path] = (sha, b3)
    return out


PINNED = pinned()


def data_file(path, data_dir):
    """The data file at `path` under BASE, read from DIR or downloaded, used
    and saved only after its SHA-256 and its BLAKE3 both match the pins."""
    sha, b3 = PINNED[path]
    local = data_dir / path if data_dir else None
    downloaded = not (local and local.exists())
    if downloaded:
        with urllib.request.urlopen(BASE + path, timeout=120) as r:
            b = r.read()
    else:
        b = local.read_bytes()
    assert hashlib.sha256(b).hexdigest() == sha, f"{path}: its SHA-256 is not the pinned one"
    assert blake3(b).hex() == b3, f"{path}: its BLAKE3 is not the pinned one"
    if downloaded and local:
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(b)
    return b.decode("utf-8-sig")


def lines(text):
    """The `fields; ...` lines of a data file, comments dropped."""
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line:
            yield [f.strip() for f in line.split(";")]


def code_points(field):
    a, _, b = field.partition("..")
    return range(int(a, 16), int(b or a, 16) + 1)


def properties(release, data_dir):
    """Every property a letter's tests read, from one release's data files."""
    read = lambda name: data_file(f"{release}/ucd/{name}", data_dir)
    p = {"category": {}, "bidi": {}, "decomposition": set(), "cased": set()}
    first = None
    for f in lines(read("UnicodeData.txt")):
        c = int(f[0], 16)
        # A range of code points is given by its first and last lines.
        span = range(first, c + 1) if f[1].endswith(", Last>") else [c]
        first = c if f[1].endswith(", First>") else None
        for x in span:
            p["category"][x], p["bidi"][x] = f[2], f[4]
        if f[5]:
            p["decomposition"].add(c)
        if f[12] or f[13] or f[14]:
            p["cased"].add(c)
    p["script"] = {c: f[1] for f in lines(read("Scripts.txt")) for c in code_points(f[0])}
    p["white_space"] = {c for f in lines(read("PropList.txt")) if f[1] == "White_Space" for c in code_points(f[0])}
    p["ignorable"] = {c for f in lines(read("DerivedCoreProperties.txt"))
                      if f[1] == "Default_Ignorable_Code_Point" for c in code_points(f[0])}
    p["maybe"] = {c for f in lines(read("DerivedNormalizationProps.txt"))
                  if f[1] in ("NFC_QC", "NFKC_QC") and len(f) > 2 and f[2] == "M" for c in code_points(f[0])}
    p["joining"] = {c: f[2] for f in lines(read("ArabicShaping.txt")) for c in code_points(f[0])}
    p["line_break"] = {c: f[1] for f in lines(read("LineBreak.txt")) for c in code_points(f[0])}
    p["word_break"] = {c: f[1] for f in lines(read("auxiliary/WordBreakProperty.txt")) for c in code_points(f[0])}
    p["width"] = {c: f[1] for f in lines(read("EastAsianWidth.txt")) for c in code_points(f[0])}
    return p


def tests(p):
    """The tests every letter passes in each release (R12), in order:
    (what it tests, which requirement, test)."""
    return [
        ("in the Basic Multilingual Plane, assigned, not a surrogate", "R6",
         lambda c: c <= 0xFFFF and c in p["category"] and p["category"][c] != "Cs"),
        ("three bytes of UTF-8", "R2", lambda c: c >= 0x800),
        ("unchanged by NFC, NFD, NFKC and NFKD, and never composed with a neighbour", "R3",
         lambda c: c not in p["decomposition"] and not 0xAC00 <= c <= 0xD7A3 and c not in p["maybe"]),
        ("a letter with no case (Lo, no case mappings)", "R3",
         lambda c: p["category"][c] == "Lo" and c not in p["cased"]),
        ("of a named script (fonts come by script)", "R7, D7",
         lambda c: p["script"].get(c) not in (None, "Common", "Inherited", "Unknown")),
        ("strongly left-to-right (bidi L)", "R4", lambda c: p["bidi"][c] == "L"),
        ("visible and non-joining", "R4",
         lambda c: c not in p["ignorable"] and c not in p["white_space"] and p["joining"].get(c, "U") == "U"),
        ("a word letter (ALetter) that never breaks a line (AL)", "R4",
         lambda c: p["word_break"].get(c) == "ALetter" and p["line_break"].get(c) == "AL"),
        ("one terminal cell (East Asian Width N)", "R2", lambda c: p["width"].get(c, "N") == "N"),
    ]


HEX = "0123456789abcdef"

# R7's measurements. font-tests/results/N.md is issue N of
# johnservil/sigil-candidates, a result the font test page sent, verbatim
# below a header; its `page` is the sigil-candidates commit whose check.html
# it ran on (the latest before the issue opened), kept as
# font-tests/pages/COMMIT.html. tools/import-fonts.py records both.
TESTS = ROOT / "alphabet" / "font-tests"
SYSTEMS = ("macOS", "iOS", "Windows", "Android", "Linux")
# The pages whose results stay out of R7: they drew each letter from its em
# box's top in a 40-pixel canvas and counted letters whose pictures matched
# as missing, so glyphs that reached past the canvas, cut alike, read as
# missing (#18, macOS: 209 of 702 Canadian letters, all drawn on macOS by
# round 0.1's pages, which counted only tofu). Their successor centres each
# letter in 96 pixels.
MISMEASURED = {"b40694415f16f8ccc8e7bdaa2c58c036940bd0d2", "cff09a58e51367e707da4f3e9a1ab67977f7bc3d"}


def system(ua):
    """The system of a browser's user agent, one of SYSTEMS (R7)."""
    return next(s for pattern, s in [(r"iPhone|iPad", "iOS"), (r"Android", "Android"), (r"Macintosh", "macOS"),
                                     (r"Windows", "Windows"), (r"Linux", "Linux")] if re.search(pattern, ua))


def page_data(commit):
    """The font test page at sigil-candidates' `commit`: {"scripts": {script:
    its letters}} and, from round 0.2, the header fields its result names
    (round, page, count, set)."""
    text = (TESTS / "pages" / f"{commit}.html").read_text(encoding="utf-8")
    for key in ("const DATA = ", "const SCRIPTS = "):
        i = text.find(key)
        if i >= 0:
            v, _ = json.JSONDecoder().raw_decode(text, i + len(key))
            if key == "const SCRIPTS = ":
                # Round 0.1: the scripts alone, and no other letters tested.
                assert "const EXTRAS = [];" in text, commit
                v = {"scripts": v}
            return v
    raise AssertionError(f"page {commit}: no letters")


def hex_ranges(field):
    out = set()
    for r in field.split():
        a, _, b = r.partition("-")
        out.update(range(int(a, 16), int(b or a, 16) + 1))
    return out


def font_result(n, text):
    """Result N (font-tests/results/N.md's text), checked line by line
    against its page: {n, ua, system, page, round, tested, missing}."""
    head, _, body = text.partition("\n\n")
    fields = dict(line.split(": ", 1) for line in head.splitlines())
    assert fields["issue"] == f"https://github.com/johnservil/sigil-candidates/issues/{n}", n
    data = page_data(fields["page"])
    # The page's result is the issue's fenced block; a note around it stays in the issue.
    block = re.search(r"```\n(.*?)\n```", body, re.S)
    assert block, f"result {n}: no result block"
    lines = [l for l in block[1].splitlines() if l.strip()]
    ua, scripts = lines[0], data["scripts"]
    if "round" in data:
        page = f", page {data['page']}" if "page" in data else ""
        assert lines[1] == f"Sigil font test {data['round']}{page}: {data['count']} candidates, set {data['set']}", n
        full = re.fullmatch(r"Drawn in full: (\d+) of (\d+) scripts", lines[2])
    else:
        full = re.fullmatch(r"Scripts drawn in full: (\d+) of (\d+)", lines[1])
    assert full and int(full[2]) == len(scripts), f"result {n}: {lines[1:3]}"
    tested, missing, seen, whole = set(), set(), set(), 0
    for line in lines[3 if "round" in data else 2:]:
        m = re.fullmatch(r"([A-Za-z_]+): (\d+)/(\d+)(?: missing ([0-9a-f -]+))?", line)
        assert m and m[1] in scripts and m[1] not in seen, f"result {n}: a line its page never writes: {line!r}"
        letters, gone = {ord(c) for c in scripts[m[1]]}, hex_ranges(m[4] or "")
        assert int(m[3]) == len(letters) and int(m[2]) + len(gone) == len(letters) and gone <= letters, f"result {n}: {line!r}"
        seen.add(m[1]); tested |= letters; missing |= gone; whole += not gone
    assert seen == set(scripts) and whole == int(full[1]), f"result {n}: its scripts are not its page's"
    return {"n": n, "ua": ua, "system": system(ua), "page": fields["page"], "round": data.get("round", "0.1"),
            "tested": tested, "missing": missing}


def font_results():
    """Every result in font-tests/results, by issue number, but those of
    MISMEASURED pages."""
    out = [font_result(int(f.stem), f.read_text(encoding="utf-8")) for f in (TESTS / "results").glob("*.md")]
    return sorted((r for r in out if r["page"] not in MISMEASURED), key=lambda r: r["n"])


def without_look_alikes(letters, skeletons):
    """D4: of each class of look-alikes the lowest code point stays; then,
    while a letter looks like a sequence of others, the one letter that ends
    the most such spellings goes (the look-alike itself, or a piece of its
    spelling; ties to the lowest code point)."""
    classes = collections.defaultdict(list)
    for c in letters:
        classes[skeletons.get(c, (c,))].append(c)
    kept = {min(cs) for cs in classes.values()}
    while True:
        spellings = sequence_look_alikes(kept, skeletons)
        if not spellings:
            return kept
        counts = collections.Counter(x for whole, pieces in spellings.items() for x in {whole} | set(pieces))
        kept.discard(max(counts, key=lambda c: (counts[c], -c)))


def sequence_look_alikes(chars, skeletons):
    """{character: the characters that spell it} for each of `chars` whose
    skeleton is the skeletons of others of `chars` in a row (one spelling
    each, the lowest code points first)."""
    skeleton = lambda c: skeletons.get(c, (c,))
    by_skeleton = {}
    for c in sorted(chars):
        by_skeleton.setdefault(skeleton(c), c)
    out = {}
    for c in chars:
        t = skeleton(c)
        if len(t) < 2:
            continue
        spelled = [[]] + [None] * len(t)
        for i in range(1, len(t) + 1):
            for j in range(i):
                piece = by_skeleton.get(tuple(t[j:i]))
                if spelled[j] is not None and piece is not None and piece != c:
                    spelled[i] = spelled[j] + [piece]
                    break
        if spelled[len(t)]:
            out[c] = spelled[len(t)]
    return out


def ranges_of(points):
    out = []
    for c in sorted(points):
        if out and out[-1][1] == c - 1:
            out[-1][1] = c
        else:
            out.append([c, c])
    return out


def main():
    args = sys.argv[1:]
    check = "--check" in args
    data_dir = Path(args[args.index("--data") + 1]) if "--data" in args else None
    newest = properties(NEWEST, data_dir)
    print(f"{'removes':>9} {'left':>9}  step (requirement)")
    left = list(range(0x110000))
    for what, ref, test in tests(newest):
        kept = [c for c in left if test(c)]
        print(f"{len(left) - len(kept):9,} {len(kept):9,}  {what} ({ref})")
        left = kept
    # R12: the same tests, passed in every release since the first.
    for release in RELEASES[:-1]:
        older = tests(properties(release, data_dir))
        left = [c for c in left if all(test(c) for _, _, test in older)]
    print(f"{'':9} {len(left):9,}  all of these in every release from {RELEASES[0]} to {NEWEST} (R12)")
    # R8: no hex digit, and nothing that looks like one (Unicode's look-alike table, UTS #39).
    skeleton = {int(f[0], 16): tuple(int(x, 16) for x in f[1].split())
                for f in lines(data_file(f"{NEWEST}/security/confusables.txt", data_dir))}
    hex_classes = {skeleton.get(ord(h), (ord(h),)) for h in HEX}
    kept = [c for c in left if skeleton.get(c, (c,)) not in hex_classes]
    print(f"{len(left) - len(kept):9,} {len(kept):9,}  no hex digit or look-alike of one (R8)")
    left = kept
    candidates = left  # what the font test page tests (candidates.txt)
    # R7: drawn by every device tested, and tested on each of the five systems.
    results = font_results()
    drawn = [c for c in left if {r["system"] for r in results if c in r["tested"]} == set(SYSTEMS)
             and not any(c in r["missing"] for r in results)]
    print(f"{len(left) - len(drawn):9,} {len(drawn):9,}  drawn on every tested device, {len(results)} results (R7)")
    # D2 within R10 and R11: as many letters as possible, a power of two, so
    # that each letter is a whole number of bits.
    size = 1 << (len(without_look_alikes(drawn, skeleton)).bit_length() - 1)
    # D7 and D4: whole scripts, the largest first (ties to the script whose
    # first letter is oldest, then by name), until the letters taken, without
    # look-alikes, reach the size.
    script, age = newest["script"], {c: tuple(map(int, f[1].split("."))) for f in
                                     lines(data_file(f"{NEWEST}/ucd/DerivedAge.txt", data_dir)) for c in code_points(f[0])}
    by_script = collections.defaultdict(list)
    for c in drawn:
        by_script[script[c]].append(c)
    order = sorted(by_script, key=lambda s: (-len(by_script[s]), min(age[c] for c in by_script[s]), s))
    taken = []
    for s in order:
        taken.append(s)
        kept = without_look_alikes([c for s in taken for c in by_script[s]], skeleton)
        if len(kept) >= size:
            break
    print(f"{len(drawn) - len(kept):9,} {len(kept):9,}  the {len(taken)} largest scripts (D7), no look-alikes (D4)")
    # D9: the oldest, ties to the lowest code point.
    letters = sorted(sorted(kept, key=lambda c: (age[c], c))[:size])
    print(f"{len(kept) - len(letters):9,} {len(letters):9,}  the oldest {size:,} (D9), "
          f"{size:,} the largest power of two R10, R11 and D2 allow")
    alphabet = "".join(map(chr, letters))
    # R5: what copying inserts, which decoding skips: white space, soft
    # hyphen, zero-width space, word joiner, byte order mark; and R4's
    # left-to-right mark, which the encoder writes before a handle (D1).
    skipped = ranges_of(newest["white_space"] | {0x00AD, 0x200B, 0x200E, 0x2060, 0xFEFF})
    assert not set(letters) & {c for a, b in skipped for c in range(a, b + 1)}, "no letter is skipped"
    source = f"Unicode {NEWEST}'s data (and every release's since {RELEASES[0]}) and alphabet/font-tests"
    # The candidates, by script: runs of consecutive code points of one script.
    runs = []
    for c in candidates:
        if runs and runs[-1][0] == newest["script"][c] and runs[-1][2] == c - 1:
            runs[-1][2] = c
        else:
            runs.append([newest["script"][c], c, c])
    outputs = {
        ROOT / "alphabet.txt": alphabet,
        ROOT / "alphabet" / "candidates.txt": (
            f"# Generated by alphabet/alphabet.py from Unicode {NEWEST}'s data (and every release's since {RELEASES[0]}); do not edit.\n"
            "# The letters that meet every constraint but R7 (drawn), which the font test page\n"
            "# tests: a script and a run of code points a line.\n"
            + "".join(f"{sc} {a:04X}..{b:04X}\n" for sc, a, b in runs)),
        ROOT / "skipped.txt": "".join(f"{a:04X}..{b:04X}\n" for a, b in skipped),
        ROOT / "lean" / "Sigil" / "Alphabet.lean": (
            f"/-! Generated by alphabet/alphabet.py from {source}; do not edit.\n\n"
            "The alphabet (`alphabet.txt`), as code points in the alphabet's order, and the code points\n"
            "decoding skips (`skipped.txt`), as [first, last] ranges. -/\n\n"
            "namespace Sigil\n\n"
            "set_option maxRecDepth 100000 in\n"
            f"def alphabet : Array Nat := #[{', '.join(str(c) for c in letters)}]\n\n"
            f"def skippedRanges : Array (Nat × Nat) := #[{', '.join(f'({a}, {b})' for a, b in skipped)}]\n\n"
            "end Sigil\n"),
        ROOT / "typescript" / "alphabet.ts": (
            f"// Generated by alphabet/alphabet.py from {source}; do not edit.\n"
            f"export const ALPHABET: string = \"{alphabet}\";\n"
            "// The code points decoding skips, as [first, last] ranges (skipped.txt).\n"
            f"export const SKIPPED: [number, number][] = {skipped};\n"),
    }
    for path, content in outputs.items():
        if check:
            assert path.read_text(encoding="utf-8") == content, f"{path.name} is not this script's output"
        else:
            path.write_text(content, encoding="utf-8")
    counts = collections.Counter(script[c] for c in letters)
    print("\n" + ", ".join(f"{s.replace('_', ' ')} {n}" for s, n in counts.most_common()))
    b = alphabet.encode("utf-8")
    print(f"{len(letters):,} letters, U+{letters[0]:04X}..U+{letters[-1]:04X}, newest from Unicode "
          f"{'.'.join(map(str, max(age[c] for c in letters)))}; alphabet.txt SHA-256 "
          f"{hashlib.sha256(b).hexdigest()}, BLAKE3 {blake3(b).hex()}" + (" (checked)" if check else ""))


if __name__ == "__main__":
    main()
