"""The base11585 alphabet, from Unicode 14.0.0's data, by the rules below.

    sh alphabet/fetch.sh DATA                  # Unicode 14.0.0's data files, into DATA
    python3 alphabet/alphabet.py DATA          # writes alphabet.txt, ignored.txt, typescript/alphabet.ts
    python3 alphabet/alphabet.py DATA --check  # checks them

Each data file is checked by SHA-256 and by BLAKE3 (blake3.py, plain Python)
before it is read, and Python's unicodedata must be Unicode 14.0.0 too; any
other input stops the program. The same inputs give the same alphabet, on
any machine. README.md explains each rule.
"""
import collections
import hashlib
import io
import sys
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import blake3

ROOT = Path(__file__).resolve().parent.parent

# Each input's SHA-256 and BLAKE3.
FILES = {
    "ArabicShaping.txt": ("c7698811e9adb6cc98fb996a7de4be2b6532f2ac67e76055cc8afdbf6ee18af3",
                          "fa1d26d40ffff0649910ac500544b721a863fa7c3d35295c7d981c62a2bd4221"),
    "DerivedAge.txt": ("7e058dec02147098bc9c28d86209f0f251bba0538f3b5a705ad02ea3bb709fe0",
                       "f022a5b165f8a8a798847636987d34e9c9349a1453ea5cfc1e53699534cd8d51"),
    "DerivedCoreProperties.txt": ("e3eddd7d469cd1b0feed7528defad1a1cc7c6a9ceb0ae4446a6d10921ed2e7bc",
                                  "ca62e64c59e8a99dd923a7f7bd5022f4a2e8102ac0505303fd4eb99cc55a497f"),
    "DerivedNormalizationProps.txt": ("b2c444c20730b097787fdf50bd7d6dd3fc5256ab8084f5b35b11c8776eca674c",
                                      "6d29c0bc8f173c916aacd435567be2e6d8319c24ec743d5b3ee6584f13fe96b6"),
    "PropList.txt": ("6bddfdb850417a5bee6deff19290fd1b138589909afb50f5a049f343bf2c6722",
                     "3ebb57bf840489327983d011cfb1e4b39e52462142f1e406816789925fee3e78"),
    "Scripts.txt": ("52db475c4ec445e73b0b16915448c357614946ad7062843c563e00d7535c6510",
                    "7d13a1c7e88acc3cd2efdde82de5cf64338bbdf9e48a5af450afb3c80175a83d"),
    "Unihan.zip": ("2ae4519b2b82cd4d15379c17e57bfb12c33c0f54da4977de03b2b04bcf11852d",
                   "239820ec391c43858fa975111870b37c4330a333ddbd6ca99cb6651b805fe5e1"),
}

UNIHAN_VARIANTS = ("kTraditionalVariant", "kSimplifiedVariant", "kZVariant", "kSemanticVariant",
                   "kSpecializedSemanticVariant", "kSpoofingVariant")


def checked(data, name):
    """A data file's bytes, after both its hashes match."""
    b = (data / name).read_bytes()
    sha, b3 = FILES[name]
    assert hashlib.sha256(b).hexdigest() == sha, f"{name}: its SHA-256 is not Unicode 14.0.0's"
    assert blake3.hash(b).hex() == b3, f"{name}: its BLAKE3 is not Unicode 14.0.0's"
    return b


def read(data, name):
    return checked(data, name).decode("utf-8")


def lines(text):
    """The `fields; ...` lines of a UCD file, comments dropped."""
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line:
            yield [f.strip() for f in line.split(";")]


def code_points(field):
    a, _, b = field.partition("..")
    return range(int(a, 16), int(b or a, 16) + 1)


def properties(data):
    """What the rules read, from the data files."""
    p = {}
    p["age"] = {c: f[1] for f in lines(read(data, "DerivedAge.txt")) for c in code_points(f[0])}
    p["script"] = {c: f[1] for f in lines(read(data, "Scripts.txt")) for c in code_points(f[0])}
    plist = collections.defaultdict(set)
    for f in lines(read(data, "PropList.txt")):
        plist[f[1]].update(code_points(f[0]))
    p["proplist"] = plist
    p["ignorable"] = {c for f in lines(read(data, "DerivedCoreProperties.txt"))
                      if f[1] == "Default_Ignorable_Code_Point" for c in code_points(f[0])}
    p["maybe"] = {c for f in lines(read(data, "DerivedNormalizationProps.txt"))
                  if f[1] in ("NFC_QC", "NFKC_QC") and len(f) > 2 and f[2] == "M" for c in code_points(f[0])}
    p["joining"] = {c: f[2] for f in lines(read(data, "ArabicShaping.txt")) for c in code_points(f[0])}
    unihan = collections.defaultdict(dict)
    with zipfile.ZipFile(io.BytesIO(checked(data, "Unihan.zip"))) as z:
        for member in ("Unihan_Variants.txt", "Unihan_IRGSources.txt"):
            for line in z.read(member).decode("utf-8").splitlines():
                if line.startswith("U+"):
                    cp, key, value = line.split("\t")
                    unihan[int(cp[2:], 16)][key] = value
    p["unihan"] = unihan
    return p


def rules(p):
    """The rules, in order: (name, the test a character must pass)."""
    hangul_jamo = [(0x1100, 0x11FF), (0xA960, 0xA97F), (0xD7B0, 0xD7FF)]

    def variants(c):
        listed = " ".join(p["unihan"][c].get(k, "") for k in UNIHAN_VARIANTS).split()
        return {int(v.split("<")[0][2:], 16) for v in listed} - {c}

    def strokes(c):
        return int(p["unihan"][c].get("kTotalStrokes", "0").split()[0])

    return [
        ("in the Basic Multilingual Plane", lambda c: c <= 0xFFFF),
        ("assigned (not a surrogate)", lambda c: c in p["age"] and not 0xD800 <= c <= 0xDFFF),
        ("a caseless letter (general category Lo)", lambda c: unicodedata.category(chr(c)) == "Lo"),
        ("strongly left-to-right (bidi class L)", lambda c: unicodedata.bidirectional(chr(c)) == "L"),
        ("unchanged by NFC, NFD, NFKC and NFKD",
         lambda c: all(unicodedata.normalize(f, chr(c)) == chr(c) for f in ("NFC", "NFD", "NFKC", "NFKD"))),
        ("unchanged by lower-casing, upper-casing and case folding",
         lambda c: chr(c).lower() == chr(c).upper() == chr(c).casefold() == chr(c)),
        ("not default-ignorable or white space",
         lambda c: c not in p["ignorable"] and c not in p["proplist"]["White_Space"]
         and c not in p["proplist"]["Pattern_White_Space"]),
        ("never the second half of a composition (no NFC or NFKC quick-check Maybe)", lambda c: c not in p["maybe"]),
        ("not a Hangul jamo", lambda c: not any(a <= c <= b for a, b in hangul_jamo)),
        ("non-joining (joining type U)", lambda c: p["joining"].get(c, "U") == "U"),
        ("not a logical-order exception", lambda c: c not in p["proplist"]["Logical_Order_Exception"]),
        ("one of Unicode 1.1's CJK Unified Ideographs (U+4E00..U+9FA5)",
         lambda c: 0x4E00 <= c <= 0x9FA5 and p["script"].get(c) == "Han" and p["age"].get(c) == "1.1"),
        ("no variant of any kind in Unihan (traditional, simplified, z-, semantic, "
         "specialized semantic, spoofing)", lambda c: not variants(c)),
        ("at least 3 strokes (kTotalStrokes)", lambda c: strokes(c) >= 3),
    ]


def alphabet(data):
    """The alphabet, ascending, and a report: each rule, and how many it removes."""
    assert unicodedata.unidata_version == "14.0.0", f"Python's unicodedata is Unicode {unicodedata.unidata_version}, not 14.0.0"
    p = properties(data)
    left = list(range(0x110000))
    report = []
    for name, test in rules(p):
        kept = [c for c in left if test(c)]
        report.append((name, len(left) - len(kept), len(kept)))
        left = kept
    return left, report, ignored(p)


def ignored(p):
    """The characters decoding ignores, as ranges: those Unicode 14.0 marks
    White_Space or Default_Ignorable_Code_Point (spaces, line ends, and the
    invisible characters software inserts: zero-width space, soft hyphen,
    word joiner, byte-order mark, variation selectors, ...). No alphabet
    character is either (the rules exclude both)."""
    cs = sorted(p["proplist"]["White_Space"] | p["ignorable"])
    ranges = []
    for c in cs:
        if ranges and ranges[-1][1] == c - 1:
            ranges[-1][1] = c
        else:
            ranges.append([c, c])
    return ranges


def typescript(chars, ranges):
    return ("// Generated by alphabet/alphabet.py from Unicode 14.0.0's data; do not edit.\n"
            f"export const ALPHABET: string = \"{chars}\";\n"
            "// The code points decoding ignores, as [first, last] ranges (ignored.txt).\n"
            f"export const IGNORED: [number, number][] = {[list(r) for r in ranges]};\n")


def main():
    data = Path(sys.argv[1])
    check = sys.argv[2:] == ["--check"]
    chars, report, ranges = alphabet(data)
    print(f"{'removes':>9} {'left':>9}  rule")
    for name, removed, left in report:
        print(f"{removed:9,} {left:9,}  {name}")
    text = "".join(chr(c) for c in chars)
    ignored_text = "".join(f"{a:04X}..{b:04X}\n" for a, b in ranges)
    assert not set(chars) & {c for a, b in ranges for c in range(a, b + 1)}, "no alphabet character is ignored"
    outputs = {ROOT / "alphabet.txt": text, ROOT / "ignored.txt": ignored_text,
               ROOT / "typescript" / "alphabet.ts": typescript(text, ranges)}
    for path, content in outputs.items():
        if check:
            assert path.read_text(encoding="utf-8") == content, f"{path} is not the rules' output"
        else:
            path.write_text(content, encoding="utf-8")
    b = text.encode("utf-8")
    print(f"\n{len(chars):,} characters, U+{chars[0]:04X}..U+{chars[-1]:04X}; alphabet.txt "
          f"SHA-256 {hashlib.sha256(b).hexdigest()}, BLAKE3 {blake3.hash(b).hex()}"
          + (" (checked)" if check else ""))


if __name__ == "__main__":
    main()
