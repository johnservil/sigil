"""Writes vectors.json and vectors.tsv, the test vectors every implementation
must pass, from this (the reference) implementation.

    python3 python/vectors.py             # writes them
    python3 python/vectors.py --check     # checks them

Deterministic: each value is SHA-256 of its length and index, so the file is
the same on every machine. "good" lists data (hex) and its text; "bad" lists
texts, the length asked for, and the error kind each must give; "variants" lists
copies that differ from a codeword (skipped characters inserted) with the data
each decodes to.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sigilcode as B

ROOT = Path(__file__).resolve().parent.parent
LENGTHS = list(range(1, 41)) + [48, 64, 100, 128]


def value(length, i):
    out = b""
    j = 0
    while len(out) < length:
        out += hashlib.sha256(f"Sigil vector {length} {i} {j}".encode()).digest()
        j += 1
    return out[:length]


# Skipped characters a copy or a line break can insert: a space, a line end,
# a tab, a carriage return, a no-break space, a zero-width space, a soft
# hyphen, a byte-order mark, a word joiner, an ideographic space, a line
# separator.
SPACES = [" ", "\n", "\t", "\r\n", "\u00a0", "\u200b", "\u00ad", "\ufeff", "\u2060", "\u3000", "\u2028"]
# Characters decoding refuses that a copy, an editor or a forger might put in
# a sigil: a hex digit, a right-to-left override, a left-to-right mark, a
# zero-width joiner, a variation selector, an ASCII letter, a CJK ideograph.
REFUSED = ["a", "\u202e", "\u200e", "\u200d", "\ufe0f", "_", "\u4e00"]


def text_of(w, n):
    """The letters that write the value w in n digits."""
    return "".join(B.ALPHABET[(w >> 11 * i) & 2047] for i in reversed(range(n)))


def marked(data, marker):
    half = 4 * len(data)
    d = int.from_bytes(data, "big")
    return (((d >> half) << 2 | marker) << half) | (d & ((1 << half) - 1))


def vectors():
    good, bad, variants = [], [], []
    for length in LENGTHS:
        datas = [bytes(length), b"\xff" * length] + [value(length, i) for i in range(3)]
        for data in datas:
            text = B.encode(data)
            good.append({"data": data.hex(), "text": text})
        # The texts of no value at this length.
        n, k = B.layout(length)
        text = B.encode(datas[2])
        bad += [
            {"text": text[:-1], "length": length, "error": "length"},
            {"text": text + text[0], "length": length, "error": "length"},
            {"text": text[:-1] + " " + "\u200b", "length": length, "error": "length"},
            {"text": text[:1] + "\u202e" + text[1:], "length": length, "error": "length"},
        ]
        bad += [{"text": c + text[1:], "length": length, "error": "character"} for c in REFUSED]
        # A multiple of K too large for the length, and the other markers.
        bad.append({"text": text_of(((1 << 11 * n) - 1) // k * k, n), "length": length, "error": "range"})
        bad += [{"text": text_of(marked(datas[2], m) * k, n), "length": length, "error": "marker"} for m in (0, 2, 3)]
        # One letter changed, and two neighbours swapped: the check catches both.
        bad.append({"text": text[:-1] + B.ALPHABET[(B.DIGIT[text[-1]] + 1) % B.N], "length": length, "error": "check"})
        j = next((j for j in range(n - 1) if text[j] != text[j + 1]), None)
        if j is not None:
            bad.append({"text": text[:j] + text[j + 1] + text[j] + text[j + 2:], "length": length, "error": "check"})
        # Copies that differ from the codeword and decode as it does: skipped
        # characters inserted.
        for insert in SPACES:
            j = length % len(text)
            variants.append({"data": datas[2].hex(), "text": insert + text[:j] + insert + text[j:] + insert})
    return {"good": good, "variants": variants, "bad": bad}


def escape(t):
    return t.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def tsv(v):
    """The same vectors as lines of tab-separated fields, for implementations
    without a JSON reader: `good DATA TEXT`, `variant DATA TEXT` (decode only)
    and `bad LENGTH ERROR TEXT`; in a text, a backslash, tab, line feed and
    carriage return are written \\\\, \\t, \\n and \\r."""
    rows = [f"good\t{g['data']}\t{escape(g['text'])}" for g in v["good"]]
    rows += [f"variant\t{g['data']}\t{escape(g['text'])}" for g in v["variants"]]
    rows += [f"bad\t{b['length']}\t{b['error']}\t{escape(b['text'])}" for b in v["bad"]]
    return "\n".join(rows) + "\n"


def main():
    v = vectors()
    outputs = {ROOT / "vectors.json": json.dumps(v, ensure_ascii=False, indent=1) + "\n", ROOT / "vectors.tsv": tsv(v)}
    for path, text in outputs.items():
        if sys.argv[1:] == ["--check"]:
            assert path.read_text(encoding="utf-8") == text, f"{path.name} is not the reference implementation's output"
        else:
            path.write_text(text, encoding="utf-8")
    print(f"vectors.json and vectors.tsv {'checked' if sys.argv[1:] == ['--check'] else 'written'}: "
          f"{len(v['good'])} good, {len(v['variants'])} variants, {len(v['bad'])} bad")


if __name__ == "__main__":
    main()
