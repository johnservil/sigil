"""The Sigil alphabet, computed from Unicode 14.0.0's data files: the whole
computation, in one script with no dependencies beyond Python 3.

    python3 alphabet/alphabet.py [--data DIR] [--check]

It downloads the data files from unicode.org (or reads them from DIR, and
saves there what it downloads), checks each by SHA-256 and by BLAKE3 (below,
in plain Python) before reading it, applies the rules, and writes
alphabet.txt, uppercase.txt, ignored.txt and typescript/alphabet.ts; with
--check it confirms that those files are its output. Every property comes
from the data files, none from Python's own tables, so the same files give
the same alphabet with any Python on any machine.
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
    "SpecialCasing.txt": ("14.0.0/ucd/SpecialCasing.txt",
                          "c667b45908fd269af25fd55d2fc5bbc157fb1b77675936e25c513ce32e080334",
                          "cec757e4847ed93cee4fbcc74f2d36b18476a2a328547a55d05b9f79abd3796d"),
    "CaseFolding.txt": ("14.0.0/ucd/CaseFolding.txt",
                        "a566cd48687b2cd897e02501118b2413c14ae86d318f9abbbba97feb84189f0f",
                        "a4d5c17de4f41245645f3a507c84c3c98a6b296304cf0598e41aa687ce2ab01c"),
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
    p = {"category": {}, "bidi": {}, "decomposition": {}, "upper": {}, "lower": {}, "fold": {}}
    for f in lines(data_file("UnicodeData.txt", data_dir)):
        c = int(f[0], 16)
        p["category"][c], p["bidi"][c] = f[2], f[4]
        if f[5]:
            p["decomposition"][c] = f[5]
        if f[12]:
            p["upper"][c] = [int(f[12], 16)]
        if f[13]:
            p["lower"][c] = [int(f[13], 16)]
    # Full case mappings where SpecialCasing gives an unconditional one.
    for f in lines(data_file("SpecialCasing.txt", data_dir)):
        if len(f) > 4 and f[4]:
            continue
        c = int(f[0], 16)
        p["lower"][c] = [int(x, 16) for x in f[1].split()]
        p["upper"][c] = [int(x, 16) for x in f[3].split()]
    for f in lines(data_file("CaseFolding.txt", data_dir)):
        if f[1] in ("C", "F"):
            p["fold"][int(f[0], 16)] = [int(x, 16) for x in f[2].split()]
    p["age"] = {c: tuple(map(int, f[1].split("."))) for f in lines(data_file("DerivedAge.txt", data_dir))
                for c in code_points(f[0])}
    p["script"] = {c: f[1] for f in lines(data_file("Scripts.txt", data_dir)) for c in code_points(f[0])}
    plist = collections.defaultdict(set)
    for f in lines(data_file("PropList.txt", data_dir)):
        plist[f[1]].update(code_points(f[0]))
    p["white_space"] = plist["White_Space"] | plist["Pattern_White_Space"]
    p["ignorable"] = {c for f in lines(data_file("DerivedCoreProperties.txt", data_dir))
                      if f[1] == "Default_Ignorable_Code_Point" for c in code_points(f[0])}
    p["maybe"] = {c for f in lines(data_file("DerivedNormalizationProps.txt", data_dir))
                  if f[1] in ("NFC_QC", "NFKC_QC") and len(f) > 2 and f[2] == "M" for c in code_points(f[0])}
    p["joining"] = {c: f[2] for f in lines(data_file("ArabicShaping.txt", data_dir)) for c in code_points(f[0])}
    p["line_break"] = {c: f[1] for f in lines(data_file("LineBreak.txt", data_dir)) for c in code_points(f[0])}
    p["word_break"] = {c: f[1] for f in lines(data_file("WordBreakProperty.txt", data_dir)) for c in code_points(f[0])}
    # Unicode's look-alike table (UTS #39): characters with one skeleton look alike.
    p["skeleton"] = {int(f[0], 16): tuple(int(x, 16) for x in f[1].split())
                     for f in lines(data_file("confusables.txt", data_dir))}
    return p


def mapping(table, c):
    return table.get(c, [c])


def rules(p):
    """The rules on single characters, in order: (what a character must be,
    the test). Each comment says what the rule protects; README.md says the
    same for readers."""
    def case_round_trip(c):
        up = mapping(p["upper"], c)
        return (mapping(p["lower"], c) == [c] and len(up) == 1 and mapping(p["lower"], up[0]) == [c]
                and mapping(p["fold"], up[0]) == mapping(p["fold"], c))

    def latin_greek_cyrillic_digit_ethiopic_canadian(c):
        return ((p["script"].get(c) in ("Latin", "Greek", "Cyrillic") and c < 0x800)
                or p["script"].get(c) in ("Ethiopic", "Canadian_Aboriginal") or 0x30 <= c <= 0x39)

    return [
        # GitHub refuses 4-byte UTF-8 in a status description, and characters
        # beyond the plane need UTF-16 surrogate pairs, which software splits.
        ("in the Basic Multilingual Plane", lambda c: c <= 0xFFFF),
        ("assigned (not a surrogate)", lambda c: c in p["category"] and p["category"][c] != "Cs"),
        # Fonts lag new letters: DejaVu, a common Linux default, lacks the
        # Cyrillic letters Unicode 6.0 and 7.0 added.
        ("assigned by Unicode 5.2 (2009) or earlier", lambda c: p["age"][c] <= (5, 2)),
        # Letters and digits survive where symbols and punctuation are
        # rewritten or dropped.
        ("a lowercase letter (Ll), a caseless letter (Lo), or an ASCII digit",
         lambda c: p["category"][c] in ("Ll", "Lo") or 0x30 <= c <= 0x39),
        # Every character displays in the order it is stored, in any paragraph.
        ("left-to-right: a letter of bidi class L, or a digit of class EN",
         lambda c: p["bidi"][c] == ("EN" if p["category"][c] == "Nd" else "L")),
        # Software normalizes text (older Mac file systems to NFD, web forms to
        # NFC). A code point with no decomposition mapping is unchanged by NFD
        # and NFKD, and so by NFC and NFKC, except the Hangul syllables, which
        # decompose by rule.
        ("unchanged by NFC, NFD, NFKC and NFKD",
         lambda c: c not in p["decomposition"] and not 0xAC00 <= c <= 0xD7A3),
        # Software that changes case leaves a codeword decodable: decoding
        # reads each letter's uppercase as the letter.
        ("its uppercase is one character, which lowercases and case-folds back to it", case_round_trip),
        # The next three exclude every way two characters interact: invisible
        # characters, two characters normalizing into one, cursive joining.
        ("neither default-ignorable nor white space", lambda c: c not in p["ignorable"] and c not in p["white_space"]),
        ("never the second half of a composition (no NFC or NFKC quick-check Maybe)", lambda c: c not in p["maybe"]),
        ("non-joining (joining type U)", lambda c: p["joining"].get(c, "U") == "U"),
        # A double-click selects the whole codeword (UAX #29 joins these).
        ("joins its neighbours into one word (word break ALetter, or Numeric for a digit)",
         lambda c: p["word_break"].get(c) in ("ALetter", "Numeric")),
        # A codeword stays on one line (UAX #14 breaks between none of these).
        ("never a line break beside its neighbours (line break AL, or NU for a digit)",
         lambda c: p["line_break"].get(c) in ("AL", "NU")),
        # A missing glyph shows as a box, and boxes hide which character is
        # which: these scripts' fonts ship on the major platforms (macOS draws
        # every Ethiopic and Canadian syllabic here; DejaVu lacks parts of the
        # Latin and Cyrillic extension blocks above U+0800).
        ("Latin, Greek or Cyrillic below U+0800, Ethiopic or Canadian syllabics, or an ASCII digit",
         latin_greek_cyrillic_digit_ethiopic_canadian),
    ]


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


def ignored_ranges(p):
    """The code points decoding ignores, as [first, last] ranges: White_Space
    and Default_Ignorable_Code_Point (spaces, line ends, and the invisible
    characters copying and line breaking insert)."""
    out = []
    for c in sorted(p["white_space"] | p["ignorable"]):
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
    for name, test in rules(p):
        kept = [c for c in left if test(c)]
        print(f"{len(left) - len(kept):9,} {len(kept):9,}  {name}")
        left = kept
    # The last two rules read the characters together. First, of each class
    # of look-alikes (characters with one skeleton in Unicode's confusables
    # table, UTS #39), only the lowest code point stays: every character a
    # person, or a machine reading a picture, compares then tells its class
    # apart from every other, and a forger must match each one exactly.
    classes = collections.defaultdict(list)
    for c in left:
        classes[p["skeleton"].get(c, (c,))].append(c)
    kept = sorted(min(cs) for cs in classes.values())
    print(f"{len(left) - len(kept):9,} {len(kept):9,}  the lowest code point of its class of look-alikes (UTS #39)")
    left = kept
    # Second, no character may look like a sequence of others: Unicode's table
    # says m looks like rn, and a syllabic with a dot like the dot final and
    # the syllabic. While some character's skeleton is the skeletons of other
    # characters in a row, the one character that ends the most such
    # spellings goes: the look-alike itself, or a piece of its spelling that
    # is outside ASCII (ties to the lowest code point).
    kept = set(left)
    while True:
        spellings = sequence_look_alikes(kept, p["skeleton"])
        if not spellings:
            break
        counts = collections.Counter(x for whole, pieces in spellings.items()
                                     for x in {whole} | {c for c in pieces if c >= 0x80})
        kept.discard(max(counts, key=lambda c: (counts[c], -c)))
    print(f"{len(left) - len(kept):9,} {len(kept):9,}  looks like no sequence of the others (UTS #39)")
    left = sorted(kept)
    letters = "".join(map(chr, left))
    upper = "".join(chr(mapping(p["upper"], c)[0]) for c in left)
    ranges = ignored_ranges(p)
    ignored = {c for a, b in ranges for c in range(a, b + 1)}
    # Decoding reads each letter or its uppercase: every one distinct, none
    # another letter, none ignored.
    assert len(set(upper)) == len(upper), "every letter has its own uppercase"
    assert not {u for u, c in zip(upper, letters) if u != c} & set(letters), "no uppercase is another letter"
    assert not {ord(x) for x in letters + upper} & ignored, "no letter or uppercase is ignored"
    outputs = {
        ROOT / "alphabet.txt": letters,
        ROOT / "uppercase.txt": upper,
        ROOT / "ignored.txt": "".join(f"{a:04X}..{b:04X}\n" for a, b in ranges),
        ROOT / "typescript" / "alphabet.ts": (
            "// Generated by alphabet/alphabet.py from Unicode 14.0.0's data; do not edit.\n"
            f"export const ALPHABET: string = \"{letters}\";\n"

            "// Each letter's uppercase, in the same order (uppercase.txt).\n"
            f"export const UPPERCASE: string = \"{upper}\";\n"
            "// The code points decoding ignores, as [first, last] ranges (ignored.txt).\n"
            f"export const IGNORED: [number, number][] = {ranges};\n"),
    }
    for path, content in outputs.items():
        if check:
            assert path.read_text(encoding="utf-8") == content, f"{path.name} is not this script's output"
        else:
            path.write_text(content, encoding="utf-8")
    print(f"\n{math.log2(len(left)):.2f} bits for each character a person compares, "
          f"{8 * math.log2(len(left)):.0f} for the first and last four")
    b = letters.encode("utf-8")
    print(f"{len(left):,} characters, U+{left[0]:04X}..U+{left[-1]:04X}; alphabet.txt SHA-256 "
          f"{hashlib.sha256(b).hexdigest()}, BLAKE3 {blake3(b).hex()}" + (" (checked)" if check else ""))


if __name__ == "__main__":
    main()
