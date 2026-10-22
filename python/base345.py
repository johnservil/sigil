"""base345: bytes of a known length as a codeword: one word of digits and
lowercase Latin, Greek and Cyrillic letters, which a double-click selects
whole and either case decodes; every one-character error and every swap of
neighbours is caught.

    encode(data) -> str                     # the codeword
    decode(codeword, length) -> bytes       # or raises DecodeError

Decoding skips white space and default-ignorable characters (ignored.txt),
which copying and line breaking insert. The specification is README.md
("The encoding"): L bytes are a number v below 2^(8L); the codeword is v * K in base N = 345,
exactly n digits, most significant first, digit d the alphabet's d-th
character (alphabet.txt, ascending), where n is the fewest digits that leave
room for a prime K larger than N and K is the largest prime at most
N^n / 2^(8L).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALPHABET = (ROOT / "alphabet.txt").read_text(encoding="utf-8")
UPPERCASE = (ROOT / "uppercase.txt").read_text(encoding="utf-8")
N = len(ALPHABET)
assert N == 345 and len(UPPERCASE) == N
# Decoding reads each letter, or its uppercase.
DIGIT = {**{c: d for d, c in enumerate(UPPERCASE)}, **{c: d for d, c in enumerate(ALPHABET)}}
# The code points decoding ignores (ignored.txt): white space and the
# default-ignorable characters, which copying and line breaking insert.
IGNORED = [tuple(int(x, 16) for x in line.split(".."))
           for line in (ROOT / "ignored.txt").read_text().split()]


def ignored(c):
    return any(a <= ord(c) <= b for a, b in IGNORED)


class DecodeError(ValueError):
    """A codeword that encodes no data of the length asked for. `kind` is
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
    assert length >= 1, "base345 encodes at least one byte"
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


def decode(codeword: str, length: int) -> bytes:
    """The `length` bytes `codeword` encodes; its white space and
    default-ignorable characters are skipped."""
    n, k = layout(length)
    chars = [(i, c) for i, c in enumerate(codeword) if not ignored(c)]
    if len(chars) != n:
        raise DecodeError("length", f"{len(chars)} characters; {length} bytes take {n}")
    w = 0
    for i, c in chars:
        if c not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(c):04X}) is not in the alphabet")
        w = w * N + DIGIT[c]
    v, r = divmod(w, k)
    if r or v >> 8 * length:
        raise DecodeError("corrupt", "the check fails: the codeword was changed")
    return v.to_bytes(length, "big")
