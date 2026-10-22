"""Writes vectors.json and vectors.tsv, the test vectors every implementation
must pass, from this (the reference) implementation.

    python3 python/vectors.py             # writes them
    python3 python/vectors.py --check     # checks them

Deterministic: each value is SHA-256 of its length and index, so the file is
the same on every machine. "good" lists data (hex) and its text; "bad" lists
texts, the length asked for, and the error kind each must give.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import base1160 as B

ROOT = Path(__file__).resolve().parent.parent
LENGTHS = list(range(1, 41)) + [48, 64, 100, 128]


def value(length, i):
    out = b""
    j = 0
    while len(out) < length:
        out += hashlib.sha256(f"base1160 vector {length} {i} {j}".encode()).digest()
        j += 1
    return out[:length]


# Ignored characters a copy or a line break can insert: a space, a line end,
# a tab, a carriage return, a no-break space, a zero-width space, a soft
# hyphen, a byte-order mark, an ideographic space, a line separator.
SPACES = [" ", "\n", "\t", "\r\n", "\u00a0", "\u200b", "\u00ad", "\ufeff", "\u3000", "\u2028"]


def vectors():
    good, bad, spaced = [], [], []
    for length in LENGTHS:
        datas = [bytes(length), b"\xff" * length] + [value(length, i) for i in range(3)]
        for data in datas:
            text = B.encode(data)
            good.append({"data": data.hex(), "text": text})
        # The corruptions of one value at this length.
        text = B.encode(datas[2])
        d = B.DIGIT[text[-1]]
        bad += [
            {"text": text[:-1], "length": length, "error": "length"},
            {"text": text + text[0], "length": length, "error": "length"},
            {"text": "a" + text[1:], "length": length, "error": "character"},
            {"text": "\u4e00" + text[1:], "length": length, "error": "character"},
            {"text": text[:-1] + B.ALPHABET[(d + 1) % B.N], "length": length, "error": "corrupt"},
        ]
        # The same text with ignored characters inserted: it decodes as before.
        # A wrong count stays wrong when the inserted characters are ignored.
        for insert in SPACES:
            j = length % len(text)
            spaced.append({"data": datas[2].hex(), "text": insert + text[:j] + insert + text[j:] + insert})
        bad.append({"text": text[:-1] + " " + "\u200b", "length": length, "error": "length"})
        swap = next((i for i in range(len(text) - 1) if text[i] != text[i + 1]), None)
        if swap is not None:
            bad.append({"text": text[:swap] + text[swap + 1] + text[swap] + text[swap + 2:], "length": length, "error": "corrupt"})
    return {"good": good, "spaced": spaced, "bad": bad}


def escape(t):
    return t.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def tsv(v):
    """The same vectors as lines of tab-separated fields, for implementations
    without a JSON reader: `good DATA TEXT`, `spaced DATA TEXT` (decode only)
    and `bad LENGTH ERROR TEXT`; in a text, a backslash, tab, line feed and
    carriage return are written \\\\, \\t, \\n and \\r."""
    rows = [f"good\t{g['data']}\t{escape(g['text'])}" for g in v["good"]]
    rows += [f"spaced\t{g['data']}\t{escape(g['text'])}" for g in v["spaced"]]
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
          f"{len(v['good'])} good, {len(v['spaced'])} spaced, {len(v['bad'])} bad")


if __name__ == "__main__":
    main()
