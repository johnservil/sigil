"""Writes vectors.json and vectors.tsv, the test vectors every implementation
must pass, from this (the reference) implementation.

    python3 python/vectors.py             # writes them
    python3 python/vectors.py --check     # checks them

Deterministic: each value is SHA-256 of its length and index, so the file is
the same on every machine. "good" lists data (hex), its form (handled or
plain) and its text; "bad" lists
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
LENGTHS = list(range(8, 41)) + [48, 64, 100, 128]


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
# separator, the left-to-right mark.
SPACES = [" ", "\n", "\t", "\r\n", "\u00a0", "\u200b", "\u00ad", "\ufeff", "\u2060", "\u3000", "\u2028", "\u200e"]
# Characters decoding refuses that a copy, an editor or a forger might put in
# a sigil's letters: a hex digit, a right-to-left override, a right-to-left
# mark, a zero-width joiner, a variation selector, an ASCII letter, a CJK
# ideograph.
REFUSED = ["a", "\u202e", "\u200f", "\u200d", "\ufe0f", "_", "\u4e00"]
# And in its handle: a letter that is no hex digit, a fullwidth digit, a
# letter of the alphabet.
REFUSED_IN_HANDLE = ["g", "\uff10", B.ALPHABET[0]]
L = 1 + B.HANDLE  # the mark and the handle, before the first letter


def parts(data):
    """(handle, rest, its bits) of `data`."""
    bits = 8 * len(data) - 4 * B.HANDLE
    d = int.from_bytes(data, "big")
    return d >> bits, d & ((1 << bits) - 1), bits


def vectors():
    good, bad, variants = [], [], []
    for length in LENGTHS:
        datas = [bytes(length), b"\xff" * length] + [value(length, i) for i in range(3)]
        for handled in (True, False):
            form = "handled" if handled else "plain"
            for data in datas:
                good.append({"form": form, "data": data.hex(), "text": B.encode(data, handled)})
            n, k = B.layout(length)
            text = B.encode(datas[2], handled)
            start = L if handled else B.PREFIX  # the first letter after the handle
            handle, rest, bits = parts(datas[2])
            r = B.offset(handle, n, k)
            write = lambda t: B.word(handle, t, n, handled)
            bad += [
                {"text": text[:-1], "length": length, "error": "length"},
                {"text": text + text[-1], "length": length, "error": "length"},
                {"text": text[:-1] + " " + "\u200b", "length": length, "error": "length"},
                {"text": text[:start + 1] + "\u202e" + text[start + 1:], "length": length, "error": "length"},
            ]
            bad += [{"text": text[:start] + c + text[start + 1:], "length": length, "error": "character"} for c in REFUSED[1:]]
            # A hex digit among the letters, and, handled, a non-hex character in the handle.
            bad.append({"text": text[:start + 1] + "a" + text[start + 2:], "length": length, "error": "character"})
            if handled:
                bad.append({"text": text[:L - 1] + text[L:], "length": length, "error": "length"})
                bad += [{"text": text[:2] + c + text[3:], "length": length, "error": "character"} for c in REFUSED_IN_HANDLE]
            else:
                # The handle's letters with the plain form's version bit of another version.
                bad.append({"text": B.letters(handle << 1 | (1 - B.PLAIN_VERSION), B.PREFIX) + text[B.PREFIX:], "length": length, "error": "marker"})
            # A value of the check too large for the length, and the other
            # markers (00, which stays unused, and 10 and 11, a successor's).
            top = ((1 << 11 * n) - 1 - r) // k * k + r
            assert top // k >> (bits + 2), "the largest checked value is out of range"
            bad.append({"text": write(top), "length": length, "error": "range"})
            bad += [{"text": write(B.marked(rest, bits, m) * k + r), "length": length, "error": "marker"}
                    for m in (0b00, 0b10, 0b11)]
            # One letter changed, one hex digit changed, and two neighbours
            # swapped: the check catches each.
            bad.append({"text": text[:-1] + B.ALPHABET[(B.DIGIT[text[-1]] + 1) % B.N], "length": length, "error": "check"})
            if handled:
                bad.append({"text": text[:L - 1] + "0123456789abcdef"[(int(text[L - 1], 16) + 1) % 16] + text[L:],
                            "length": length, "error": "check"})
            j = next((j for j in range(start, len(text) - 1) if text[j] != text[j + 1]), None)
            if j is not None:
                bad.append({"text": text[:j] + text[j + 1] + text[j] + text[j + 2:], "length": length, "error": "check"})
            # Copies that differ from the codeword and decode as it does:
            # skipped characters inserted; handled, the mark gone, the handle
            # in uppercase.
            for insert in SPACES:
                j = start + 1 + length % (len(text) - start - 1)
                variants.append({"data": datas[2].hex(), "text": insert + text[:j] + insert + text[j:] + insert})
            if handled:
                variants.append({"data": datas[2].hex(), "text": text[1:]})
                variants.append({"data": datas[2].hex(), "text": text[:1] + text[1:L].upper() + text[L:]})
    return {"good": good, "variants": variants, "bad": bad}


def escape(t):
    return t.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def tsv(v):
    """The same vectors as lines of tab-separated fields, for implementations
    without a JSON reader: `good FORM DATA TEXT` (FORM handled or plain),
    `variant DATA TEXT` (decode only)
    and `bad LENGTH ERROR TEXT`; in a text, a backslash, tab, line feed and
    carriage return are written \\\\, \\t, \\n and \\r."""
    rows = [f"good\t{g['form']}\t{g['data']}\t{escape(g['text'])}" for g in v["good"]]
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
