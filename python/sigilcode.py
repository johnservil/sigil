"""Sigil: bytes of a known length written as a sigil, one word of letters and
digits that a double-click selects whole, with no two characters alike, and
a check that confirms a reading or picks the right one of several.

    encode(data) -> str                          # the sigil
    decode(sigil, length) -> bytes               # or raises DecodeError
    decode_readings(readings, length) -> list    # every reading that decodes

The specification is README.md ("The encoding"). The data, joined by a
check (BLAKE3 of the data), is written in base N = 1,353: one character
more than the data needs, the check taking all the room left (for 32 bytes,
26 characters and a 14-bit check). Decoding skips white space
and default-ignorable characters (ignored.txt) and reads a letter's
uppercase as the letter.

For maintainers: Sigil writes the data in order, without jumbling it.
README.md ("Telling sigils apart", "Why Sigil writes the data in order")
says what jumbling would and would not accomplish, case by case, and why
Sigil leaves it to the callers whose data needs it; read it before adding
any mixing of the data to the encoding.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALPHABET = (ROOT / "alphabet.txt").read_text(encoding="utf-8")
UPPERCASE = (ROOT / "uppercase.txt").read_text(encoding="utf-8")
N = len(ALPHABET)
assert N == 1353 and len(UPPERCASE) == N
DIGIT = {**{c: d for d, c in enumerate(UPPERCASE)}, **{c: d for d, c in enumerate(ALPHABET)}}
IGNORED = [tuple(int(x, 16) for x in line.split("..")) for line in (ROOT / "ignored.txt").read_text().split()]


class DecodeError(ValueError):
    """A sigil that encodes no data of the length asked for. `kind` is
    "length" (the wrong number of characters), "character" (one outside the
    alphabet), "range" (a value too large for the length), or "check" (the
    check fails: a character was misread or changed)."""
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


# BLAKE3 (github.com/BLAKE3-team/BLAKE3-specs) and its derive-key mode, which
# the check uses. test.py checks it against BLAKE3's official test vectors.

IV = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8]
CHUNK_START, CHUNK_END, PARENT, ROOT_FLAG, KEYED = 1, 2, 4, 8, 16
DERIVE_KEY_CONTEXT, DERIVE_KEY_MATERIAL = 32, 64
M32 = 0xFFFFFFFF


def _g(s, a, b, c, d, x, y):
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


def _compress(cv, m, counter, block_len, flags):
    s = cv[:8] + IV[:4] + [counter & M32, counter >> 32 & M32, block_len, flags]
    for r in range(7):
        _g(s, 0, 4, 8, 12, m[0], m[1]); _g(s, 1, 5, 9, 13, m[2], m[3])
        _g(s, 2, 6, 10, 14, m[4], m[5]); _g(s, 3, 7, 11, 15, m[6], m[7])
        _g(s, 0, 5, 10, 15, m[8], m[9]); _g(s, 1, 6, 11, 12, m[10], m[11])
        _g(s, 2, 7, 8, 13, m[12], m[13]); _g(s, 3, 4, 9, 14, m[14], m[15])
        if r < 6:
            m = [m[i] for i in PERMUTATION]
    return [s[i] ^ s[i + 8] for i in range(8)] + [s[i + 8] ^ cv[i] for i in range(8)]


def _words(block):
    block = block + bytes(64 - len(block))
    return [int.from_bytes(block[4 * i:4 * i + 4], "little") for i in range(16)]


def _blake3(data, key, flags, length):
    """BLAKE3's output of `length` bytes for `data`, under key words `key` and
    mode `flags` (0 for hashing, KEYED, or a derive-key flag)."""
    def chunk(c, counter):
        cv = key
        blocks = [c[i:i + 64] for i in range(0, len(c), 64)] or [b""]
        for i, block in enumerate(blocks):
            f = flags | (CHUNK_START if i == 0 else 0) | (CHUNK_END if i == len(blocks) - 1 else 0)
            if i == len(blocks) - 1:
                return (cv, _words(block), counter, len(block), f)
            cv = _compress(cv, _words(block), counter, 64, f)[:8]

    def cv_of(out):
        return _compress(*out)[:8]

    chunks = [data[i:i + 1024] for i in range(0, len(data), 1024)] or [b""]
    stack = []
    for i, c in enumerate(chunks[:-1]):
        cv, total = cv_of(chunk(c, i)), i + 1
        while total & 1 == 0:
            cv = cv_of((key, stack.pop() + cv, 0, 64, flags | PARENT))
            total >>= 1
        stack.append(cv)
    out = chunk(chunks[-1], len(chunks) - 1)
    while stack:
        out = (key, stack.pop() + cv_of(out), 0, 64, flags | PARENT)
    cv, m, _, block_len, f = out
    result = bytearray()
    counter = 0
    while len(result) < length:
        result += b"".join(w.to_bytes(4, "little") for w in _compress(cv, m, counter, block_len, f | ROOT_FLAG))
        counter += 1
    return bytes(result[:length])


def blake3_hash(data, length=32):
    return _blake3(data, IV, 0, length)


def blake3_derive_key(context, material, length=32):
    """BLAKE3's derive-key mode: `length` bytes from key material under a
    context string."""
    context_key = _blake3(context.encode("utf-8"), IV, DERIVE_KEY_CONTEXT, 32)
    key = [int.from_bytes(context_key[4 * i:4 * i + 4], "little") for i in range(8)]
    return _blake3(material, key, DERIVE_KEY_MATERIAL, length)


def layout(length):
    """(n, c) for data of `length` bytes (at least 1): the sigil's
    characters, one more than the fewest that hold 8 * length bits, and the
    check's bits, all the room left: the most c with 2^(8 * length + c) <= N^n."""
    assert length >= 1, "Sigil encodes at least one byte"
    m = 1
    while N ** m < 2 ** (8 * length):
        m += 1
    n = m + 1
    c = (N ** n).bit_length() - 1 - 8 * length
    return n, c


def check(data, c):
    """The check: the first c bits of BLAKE3, in derive-key mode, over the
    data."""
    return int.from_bytes(blake3_derive_key("Sigil 2026-10-22 check", data, 8), "big") >> (64 - c)


def encode(data: bytes) -> str:
    n, c = layout(len(data))
    w = int.from_bytes(data, "big") << c | check(data, c)
    out = []
    for _ in range(n):
        w, d = divmod(w, N)
        out.append(ALPHABET[d])
    return "".join(reversed(out))


def ignored(ch):
    return any(a <= ord(ch) <= b for a, b in IGNORED)


def decode(sigil: str, length: int) -> bytes:
    """The `length` bytes `sigil` encodes; its white space and
    default-ignorable characters are skipped, and a letter's uppercase reads
    as the letter."""
    n, c = layout(length)
    chars = [(i, ch) for i, ch in enumerate(sigil) if not ignored(ch)]
    if len(chars) != n:
        raise DecodeError("length", f"{len(chars)} characters; {length} bytes take {n}")
    w = 0
    for i, ch in chars:
        if ch not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(ch):04X}) is not in the alphabet")
        w = w * N + DIGIT[ch]
    if w >> (8 * length + c):
        raise DecodeError("range", f"its value is too large for {length} bytes: a character was misread or changed")
    data = (w >> c).to_bytes(length, "big")
    if w & ((1 << c) - 1) != check(data, c):
        raise DecodeError("check", "the check fails: a character was misread or changed")
    return data


def decode_readings(readings, length):
    """Every data of `length` bytes that some reading decodes to, for a
    reader unsure of some characters (an OCR tool, say): `readings` gives
    each character's possible readings, one string a character, the
    likeliest first. One result is the answer; more mean the readings leave
    the sigil ambiguous. The work is the product of the readings' counts."""
    import itertools
    found = []
    for choice in itertools.product(*readings):
        try:
            data = decode("".join(choice), length)
        except DecodeError:
            continue
        if data not in found:
            found.append(data)
    return found
