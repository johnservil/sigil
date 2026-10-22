"""base11585: bytes of a known length as text, one of 11,585 CJK ideographs a
character, every one-character error and every swap of neighbours caught.

    encode(data) -> str
    decode(text, length) -> bytes      # or raises DecodeError; white space is skipped

The specification is README.md ("The encoding"): L bytes are a number v
below 2^(8L); the text is v * K in base N = 11,585, exactly n digits, most
significant first, digit d the alphabet's d-th character (alphabet.txt,
ascending), where n is the fewest digits that leave room for a prime K
larger than N and K is the largest prime at most N^n / 2^(8L).
"""
from pathlib import Path

ALPHABET = (Path(__file__).resolve().parent.parent / "alphabet.txt").read_text(encoding="utf-8")
N = len(ALPHABET)
assert N == 11585
DIGIT = {c: d for d, c in enumerate(ALPHABET)}
# The code points decoding ignores (ignored.txt): white space and the
# default-ignorable characters, which copying and line breaking insert.
IGNORED = [tuple(int(x, 16) for x in line.split(".."))
           for line in (Path(__file__).resolve().parent.parent / "ignored.txt").read_text().split()]


def ignored(c):
    return any(a <= ord(c) <= b for a, b in IGNORED)


class DecodeError(ValueError):
    """A text that encodes no data of the length asked for. `kind` is
    "length" (the wrong number of characters), "character" (one outside the
    alphabet), or "corrupt" (the check fails)."""
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def is_prime(k):
    if k < 2:
        return False
    d = 2
    while d * d <= k:
        if k % d == 0:
            return False
        d += 1
    return True


def layout(length):
    """(n, K) for data of `length` bytes (at least 1)."""
    assert length >= 1, "base11585 encodes at least one byte"
    n = 1
    while (N ** n >> 8 * length) <= N:
        n += 1
    k = N ** n >> 8 * length
    while not is_prime(k):
        k -= 1
    return n, k


def encode(data: bytes) -> str:
    n, k = layout(len(data))
    w = int.from_bytes(data, "big") * k
    out = []
    for _ in range(n):
        w, d = divmod(w, N)
        out.append(ALPHABET[d])
    return "".join(reversed(out))


def decode(text: str, length: int) -> bytes:
    """`text`'s white space and default-ignorable characters are skipped."""
    n, k = layout(length)
    chars = [(i, c) for i, c in enumerate(text) if not ignored(c)]
    if len(chars) != n:
        raise DecodeError("length", f"{len(chars)} characters; {length} bytes take {n}")
    w = 0
    for i, c in chars:
        if c not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(c):04X}) is not in the alphabet")
        w = w * N + DIGIT[c]
    v, r = divmod(w, k)
    if r or v >> 8 * length:
        raise DecodeError("corrupt", "the check fails: the text was changed")
    return v.to_bytes(length, "big")
