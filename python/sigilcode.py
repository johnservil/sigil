"""Sigil: bytes of a known length written as a sigil, one word of letters and
digits that a double-click selects whole, with no two characters alike, and
a check that confirms a reading or picks the right one of several.

    encode(data) -> str                          # the sigil
    decode(sigil, length) -> bytes               # or raises DecodeError
    decode_readings(readings, length) -> list    # every reading that decodes

The specification is README.md ("The encoding"). The data, multiplied by a
prime K larger than N, is written in base N = 1,353, in the fewest
characters that leave room for such a K: one more than the data needs, at
almost every length (for 32 bytes, 26 characters and K = 22,381). A
decoder checks that the value is a multiple of K, which catches every
changed character and every swap of neighbours, and lets decode_readings
recover any one character from all its possible readings. Decoding skips
white space and default-ignorable characters (ignored.txt) and reads a
letter's uppercase as the letter.

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


def is_prime(k):
    return k > 1 and all(k % p for p in range(2, int(k ** 0.5) + 1))


# The smallest prime larger than N: K must exceed N (README.md, "Why the
# check catches what it does").
LEAST_K = next(k for k in range(N + 1, 2 * N) if is_prime(k))


def layout(length):
    """(n, K) for data of `length` bytes (at least 1): the sigil's
    characters, the fewest whose room R = floor(N^n / 2^(8 * length)) holds a
    prime larger than N, and K, the largest prime at most R."""
    assert length >= 1, "Sigil encodes at least one byte"
    n = 1
    while N ** n >> 8 * length < LEAST_K:
        n += 1
    k = N ** n >> 8 * length
    while not is_prime(k):
        k -= 1
    return n, k


def encode(data: bytes) -> str:
    """`data`'s sigil, layout(len(data))[0] characters of the alphabet.
    Its protection against look-alikes holds for data that looks random (a
    secure hash's output, a key, a random identifier): hash or jumble structured data
    before encoding it (README.md, "Data with structure: hash it, or jumble it")."""
    n, k = layout(len(data))
    w = int.from_bytes(data, "big") * k
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
    n, k = layout(length)
    chars = [(i, ch) for i, ch in enumerate(sigil) if not ignored(ch)]
    if len(chars) != n:
        raise DecodeError("length", f"{len(chars)} characters; {length} bytes take {n}")
    w = 0
    for i, ch in chars:
        if ch not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(ch):04X}) is not in the alphabet")
        w = w * N + DIGIT[ch]
    if w >= k << 8 * length:
        raise DecodeError("range", f"its value is too large for {length} bytes: a character was misread or changed")
    if w % k:
        raise DecodeError("check", "the check fails: a character was misread or changed")
    return (w // k).to_bytes(length, "big")


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
