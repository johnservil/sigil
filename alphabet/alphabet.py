"""The Sigil alphabet, computed from Unicode 14.0.0's data files and the font
tests in fonts.txt by the rules of RULES.md: the whole computation, in one
script with no dependencies beyond Python 3.

    python3 alphabet/alphabet.py [--data DIR] [--check]

It downloads the data files from unicode.org (or reads them from DIR, and
saves there what it downloads), checks each by SHA-256 and by BLAKE3 (below,
in plain Python) before reading it, applies the rules, and writes
alphabet.txt, skipped.txt, typescript/alphabet.ts and lean/Sigil/Alphabet.lean;
with --check it confirms that those files are its output. Every property
comes from the data files, none from Python's own tables, so the same files
give the same alphabet with any Python on any machine.
"""
import collections
import hashlib
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.unicode.org/Public/"

# Each data file's path under BASE, SHA-256, and BLAKE3.
FILES = {
    "UnicodeData.txt": ("14.0.0/ucd/UnicodeData.txt",
                        "36018e68657fdcb3485f636630ffe8c8532e01c977703d2803f5b89d6c5feafb",
                        "769f79943efcbeeb922a0ea4b6e1e1240ef3815ed5b8e7b736008528ca12bbf3"),
    "DerivedAge.txt": ("14.0.0/ucd/DerivedAge.txt",
                       "7e058dec02147098bc9c28d86209f0f251bba0538f3b5a705ad02ea3bb709fe0",
                       "f022a5b165f8a8a798847636987d34e9c9349a1453ea5cfc1e53699534cd8d51"),
    "Scripts.txt": ("14.0.0/ucd/Scripts.txt",
                    "52db475c4ec445e73b0b16915448c357614946ad7062843c563e00d7535c6510",
                    "7d13a1c7e88acc3cd2efdde82de5cf64338bbdf9e48a5af450afb3c80175a83d"),
    "PropList.txt": ("14.0.0/ucd/PropList.txt",
                     "6bddfdb850417a5bee6deff19290fd1b138589909afb50f5a049f343bf2c6722",
                     "3ebb57bf840489327983d011cfb1e4b39e52462142f1e406816789925fee3e78"),
    "DerivedCoreProperties.txt": ("14.0.0/ucd/DerivedCoreProperties.txt",
                                  "e3eddd7d469cd1b0feed7528defad1a1cc7c6a9ceb0ae4446a6d10921ed2e7bc",
                                  "ca62e64c59e8a99dd923a7f7bd5022f4a2e8102ac0505303fd4eb99cc55a497f"),
    "DerivedNormalizationProps.txt": ("14.0.0/ucd/DerivedNormalizationProps.txt",
                                      "b2c444c20730b097787fdf50bd7d6dd3fc5256ab8084f5b35b11c8776eca674c",
                                      "6d29c0bc8f173c916aacd435567be2e6d8319c24ec743d5b3ee6584f13fe96b6"),
    "ArabicShaping.txt": ("14.0.0/ucd/ArabicShaping.txt",
                          "c7698811e9adb6cc98fb996a7de4be2b6532f2ac67e76055cc8afdbf6ee18af3",
                          "fa1d26d40ffff0649910ac500544b721a863fa7c3d35295c7d981c62a2bd4221"),
    "LineBreak.txt": ("14.0.0/ucd/LineBreak.txt",
                      "9e06e9f35c6959fb91dcc7993f90d58523c3079bc62c6b25f828b4cdebc5d70c",
                      "9119eb1c4d405f6f6a9a805a28d70925007be6cfd3bcd18e16a051eef1daba82"),
    "WordBreakProperty.txt": ("14.0.0/ucd/auxiliary/WordBreakProperty.txt",
                              "7716752aad296d4ab23ff4ed0a2746fc5328750ff84e9e7d6f3828ee9eaef742",
                              "54ad33216c49a8d47c4b323c546143d91810ff4cee04da7b8c0d97e882d0a1ae"),
    "EastAsianWidth.txt": ("14.0.0/ucd/EastAsianWidth.txt",
                           "f901ac011aa32a09224d6555da71e2532c59c1d3381322829de0e3b880507250",
                           "d4244c1205359fee66cf578d2cd03b0364a6ea5602e9f6b670d6b06631b63133"),
    "confusables.txt": ("security/14.0.0/confusables.txt",
                        "f901938af166c3afa471bd10c224b0979cd024340f290649e16b29f779d48bfe",
                        "8ea02bbe19f01d541a6387ab97b5f8ebf265fd794460c658679264ae5e7024ec"),
}



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


def data_file(name, data_dir):
    """A data file's text, read from DIR or downloaded, used and saved only
    after its SHA-256 and its BLAKE3 both match."""
    path, sha, b3 = FILES[name]
    local = data_dir / name if data_dir else None
    downloaded = not (local and local.exists())
    if downloaded:
        with urllib.request.urlopen(BASE + path, timeout=120) as r:
            b = r.read()
    else:
        b = local.read_bytes()
    assert hashlib.sha256(b).hexdigest() == sha, f"{name}: its SHA-256 is not Unicode 14.0.0's"
    assert blake3(b).hex() == b3, f"{name}: its BLAKE3 is not Unicode 14.0.0's"
    if downloaded and local:
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


def properties(data_dir):
    """Every property the rules read, from the data files."""
    p = {"category": {}, "bidi": {}, "decomposition": {}}
    for f in lines(data_file("UnicodeData.txt", data_dir)):
        c = int(f[0], 16)
        p["category"][c], p["bidi"][c] = f[2], f[4]
        if f[5]:
            p["decomposition"][c] = f[5]
    p["age"] = {c: tuple(map(int, f[1].split("."))) for f in lines(data_file("DerivedAge.txt", data_dir))
                for c in code_points(f[0])}
    p["script"] = {c: f[1] for f in lines(data_file("Scripts.txt", data_dir)) for c in code_points(f[0])}
    plist = collections.defaultdict(set)
    for f in lines(data_file("PropList.txt", data_dir)):
        plist[f[1]].update(code_points(f[0]))
    p["white_space"] = plist["White_Space"]
    p["ignorable"] = {c for f in lines(data_file("DerivedCoreProperties.txt", data_dir))
                      if f[1] == "Default_Ignorable_Code_Point" for c in code_points(f[0])}
    p["maybe"] = {c for f in lines(data_file("DerivedNormalizationProps.txt", data_dir))
                  if f[1] in ("NFC_QC", "NFKC_QC") and len(f) > 2 and f[2] == "M" for c in code_points(f[0])}
    p["joining"] = {c: f[2] for f in lines(data_file("ArabicShaping.txt", data_dir)) for c in code_points(f[0])}
    p["line_break"] = {c: f[1] for f in lines(data_file("LineBreak.txt", data_dir)) for c in code_points(f[0])}
    p["word_break"] = {c: f[1] for f in lines(data_file("WordBreakProperty.txt", data_dir)) for c in code_points(f[0])}
    p["width"] = {c: f[1] for f in lines(data_file("EastAsianWidth.txt", data_dir)) for c in code_points(f[0])}
    # Unicode's look-alike table (UTS #39): characters with one skeleton look alike.
    p["skeleton"] = {int(f[0], 16): tuple(int(x, 16) for x in f[1].split())
                     for f in lines(data_file("confusables.txt", data_dir))}
    return p


HEX = "0123456789abcdef"
SYSTEMS = ("macOS", "iOS", "Windows", "Android", "Linux")
SIZE = 2048


def constraints(p):
    """RULES.md's constraints on single letters, in order: (name, test)."""
    hex_classes = {p["skeleton"].get(ord(h), (ord(h),)) for h in HEX}
    return [
        ("C1 in the Basic Multilingual Plane, assigned, not a surrogate",
         lambda c: c <= 0xFFFF and c in p["category"] and p["category"][c] != "Cs"),
        ("C2 unchanged by NFC, NFD, NFKC and NFKD",
         lambda c: c not in p["decomposition"] and not 0xAC00 <= c <= 0xD7A3),
        ("C3 a caseless letter (Lo) of a named script",
         lambda c: p["category"][c] == "Lo" and p["script"].get(c) not in (None, "Common", "Inherited")),
        ("C4 strongly left-to-right (bidi L)", lambda c: p["bidi"][c] == "L"),
        ("C5 visible, never the second half of a composition, non-joining",
         lambda c: c not in p["ignorable"] and c not in p["white_space"] and c not in p["maybe"]
         and p["joining"].get(c, "U") == "U"),
        ("C6 a word letter (ALetter) that never breaks a line (AL)",
         lambda c: p["word_break"].get(c) == "ALetter" and p["line_break"].get(c) == "AL"),
        ("C7 one terminal cell (East Asian Width N)", lambda c: p["width"].get(c, "N") == "N"),
        ("C8 three bytes of UTF-8", lambda c: 0x800 <= c <= 0xFFFF),
        ("C10 no hex digit or look-alike of one", lambda c: p["skeleton"].get(c, (c,)) not in hex_classes),
    ]


def fonts(path):
    """fonts.txt's results: [(name, system, tested, missing)]."""
    def ranges(field):
        out = set()
        for r in field.split():
            a, _, b = r.partition("-")
            out.update(range(int(a, 16), int(b or a, 16) + 1))
        return out
    results, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("result "):
            _, n, date, system, browser = line.split(" ")
            assert system in SYSTEMS, line
            cur = {"name": f"#{n} {system} {browser} {date}", "system": system}
            results.append(cur)
        elif line.startswith("tested "):
            cur["tested"] = ranges(line[7:])
        elif line.startswith("missing"):
            cur["missing"] = ranges(line[8:])
    return results


def without_look_alikes(letters, skeletons):
    """G3: of each class of look-alikes the lowest code point stays; then, while
    a letter looks like a sequence of others, the one letter that ends the most
    such spellings goes (the look-alike itself, or a piece of its spelling;
    ties to the lowest code point)."""
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
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
    p = properties(data_dir)
    left = list(range(0x110000))
    print(f"{'removes':>9} {'left':>9}  rule")
    for name, test in constraints(p):
        kept = [c for c in left if test(c)]
        print(f"{len(left) - len(kept):9,} {len(kept):9,}  {name}")
        left = kept
    # G1: letters every tested device drew, tested on each of the five systems.
    results = fonts(ROOT / "alphabet" / "fonts.txt")
    drawn = [c for c in left if {r["system"] for r in results if c in r["tested"]} == set(SYSTEMS)
             and not any(c in r["missing"] for r in results)]
    print(f"{len(left) - len(drawn):9,} {len(drawn):9,}  G1 drawn on every tested device ({len(results)} results)")
    # G2 and G3: whole scripts, the largest first, until the letters taken, without look-alikes, reach SIZE.
    by_script = collections.defaultdict(list)
    for c in drawn:
        by_script[p["script"][c]].append(c)
    order = sorted(by_script, key=lambda s: (-len(by_script[s]), min(p["age"][c] for c in by_script[s]), s))
    taken = []
    for script in order:
        taken.append(script)
        kept = without_look_alikes([c for s in taken for c in by_script[s]], p["skeleton"])
        if len(kept) >= SIZE:
            break
    assert len(kept) >= SIZE, "the scripts drawn everywhere hold too few letters"
    print(f"{len(drawn) - len(kept):9,} {len(kept):9,}  G2 the {len(taken)} largest scripts; G3 no look-alikes among them")
    # G4: the SIZE oldest, ties to the lowest code point.
    letters = sorted(sorted(kept, key=lambda c: (p["age"][c], c))[:SIZE])
    print(f"{len(kept) - len(letters):9,} {len(letters):9,}  G4 the oldest {SIZE:,}")
    alphabet = "".join(map(chr, letters))
    skipped = ranges_of(p["white_space"] | {0x00AD, 0x200B, 0x2060, 0xFEFF})
    assert not set(letters) & {c for a, b in skipped for c in range(a, b + 1)}, "no letter is skipped"
    outputs = {
        ROOT / "alphabet.txt": alphabet,
        ROOT / "skipped.txt": "".join(f"{a:04X}..{b:04X}\n" for a, b in skipped),
        ROOT / "lean" / "Sigil" / "Alphabet.lean": (
            "/-! Generated by alphabet/alphabet.py from Unicode 14.0.0's data and alphabet/fonts.txt; do not edit.\n\n"
            "The alphabet (`alphabet.txt`), as code points in the alphabet's order, and the code points\n"
            "decoding skips (`skipped.txt`), as [first, last] ranges. -/\n\n"
            "namespace Sigil\n\n"
            "set_option maxRecDepth 100000 in\n"
            f"def alphabet : Array Nat := #[{', '.join(str(c) for c in letters)}]\n\n"
            f"def skippedRanges : Array (Nat × Nat) := #[{', '.join(f'({a}, {b})' for a, b in skipped)}]\n\n"
            "end Sigil\n"),
        ROOT / "typescript" / "alphabet.ts": (
            "// Generated by alphabet/alphabet.py from Unicode 14.0.0's data and alphabet/fonts.txt; do not edit.\n"
            f"export const ALPHABET: string = \"{alphabet}\";\n"
            "// The code points decoding skips, as [first, last] ranges (skipped.txt).\n"
            f"export const SKIPPED: [number, number][] = {skipped};\n"),
    }
    for path, content in outputs.items():
        if check:
            assert path.read_text(encoding="utf-8") == content, f"{path.name} is not this script's output"
        else:
            path.write_text(content, encoding="utf-8")
    scripts = collections.Counter(p["script"][c] for c in letters)
    print("\n" + ", ".join(f"{s.replace('_', ' ')} {n}" for s, n in scripts.most_common()))
    b = alphabet.encode("utf-8")
    print(f"{len(letters):,} letters, U+{letters[0]:04X}..U+{letters[-1]:04X}, newest from Unicode "
          f"{'.'.join(map(str, max(p['age'][c] for c in letters)))}; alphabet.txt SHA-256 "
          f"{hashlib.sha256(b).hexdigest()}, BLAKE3 {blake3(b).hex()}" + (" (checked)" if check else ""))


if __name__ == "__main__":
    main()
