"""Sigil: bytes of a known length written as a sigil, one word of letters that
a double-click selects whole, with no two letters alike, and a check that
confirms a reading or picks the right one of several.

    encode(data) -> str                           # the sigil
    decode(sigil, length) -> bytes                # or raises DecodeError
    decode_readings(readings, length) -> bytes    # the one reading that decodes

This is the reference implementation; the specification is README.md ("The
encoding"). The data, with the marker bits 01 between its high and low
halves, is multiplied by a prime K larger than N and written in base
N = 2,048, 11 bits a letter, in n = ceil((8 * length + 14) / 11) letters. A
decoder checks that the value is a multiple of K, which catches every
changed letter and every swap of neighbours, and that the marker is 01.
Decoding skips the characters of skipped.txt (white space, and four
invisible characters copying inserts), and nothing else outside the
alphabet.

For maintainers: Sigil writes the data in order, without jumbling it.
README.md ("Telling sigils apart", "Why Sigil writes the data in order")
says what jumbling would and would not accomplish, case by case, and why
Sigil leaves it to the callers whose data needs it; read it before adding
any mixing of the data to the encoding.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALPHABET = (ROOT / "alphabet.txt").read_text(encoding="utf-8")
N = len(ALPHABET)
assert N == 2048
DIGIT = {c: d for d, c in enumerate(ALPHABET)}
SKIPPED = [tuple(int(x, 16) for x in line.split("..")) for line in (ROOT / "skipped.txt").read_text().split()]
MARKER = 0b01


class DecodeError(ValueError):
    """A sigil that encodes no data of the length asked for. `kind` is
    "length" (the wrong number of letters), "character" (one outside the
    alphabet), "check" (the check fails: a letter was misread or changed),
    "range" (a value too large for the length), "marker" (a string of another
    format, or a changed letter), or, from decode_readings, "ambiguous" (the
    readings leave several data)."""
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def is_prime(k):
    return k > 1 and all(k % p for p in range(2, int(k ** 0.5) + 1))


def escapes(k, m):
    """The changes (d1, d2) to two letters, each by less than N, that a check
    by k misses when the first letter's place is m times the second's
    (modulo k): d1 * m + d2 = 0 (mod k)."""
    hits = 0
    for d1 in range(1, N):
        r = -d1 * m % k
        hits += 0 < r < N or k - N < r
    return 2 * hits


def check_prime(room):
    """K for a room: the largest prime at most it, larger than N, whose worst
    letter distance, 1 to 63 letters apart, lets through at most twice the
    two-letter changes a random multiplier would, about (2N - 2)^2 / K. (The
    largest prime alone sits just below a power of two, where some distance's
    multiplier is a small number and many two-letter changes escape.)"""
    k = room
    while True:
        if k > N and is_prime(k):
            if max(escapes(k, pow(2, 11 * dist, k)) for dist in range(1, 64)) * k <= 2 * (2 * N - 2) ** 2:
                return k
        k -= 1


CHECK_PRIMES = {}


def layout(length):
    """(n, K) for data of `length` bytes (at least 1): the sigil's letters,
    the fewest whose room 2^(11n - 8 * length - 2) holds a prime larger than
    N (2,053 or more), and K, check_prime(room)."""
    assert length >= 1, "Sigil encodes at least one byte"
    n = -(-(8 * length + 14) // 11)
    room = 1 << (11 * n - 8 * length - 2)
    if room not in CHECK_PRIMES:
        CHECK_PRIMES[room] = check_prime(room)
    return n, CHECK_PRIMES[room]


def encode(data: bytes) -> str:
    """`data`'s sigil, layout(len(data))[0] letters of the alphabet. Its
    protection against look-alikes holds for data that looks random (a
    secure hash's output, a key, a random identifier): hash or jumble
    structured data before encoding it (README.md, "Data with structure")."""
    n, k = layout(len(data))
    half = 4 * len(data)
    d = int.from_bytes(data, "big")
    w = ((((d >> half) << 2 | MARKER) << half) | (d & ((1 << half) - 1))) * k
    return "".join(ALPHABET[(w >> 11 * i) & 2047] for i in reversed(range(n)))


def skipped(ch):
    return any(a <= ord(ch) <= b for a, b in SKIPPED)


def decode(sigil: str, length: int) -> bytes:
    """The `length` bytes `sigil` encodes; the characters of skipped.txt in
    it are skipped."""
    n, k = layout(length)
    letters = [(i, ch) for i, ch in enumerate(sigil) if not skipped(ch)]
    if len(letters) != n:
        raise DecodeError("length", f"{len(letters)} letters; {length} bytes take {n}")
    w = 0
    for i, ch in letters:
        if ch not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(ch):04X}) is not a letter of the alphabet")
        w = w << 11 | DIGIT[ch]
    if w % k:
        raise DecodeError("check", "the check fails: a letter was misread or changed")
    marked, half = w // k, 4 * length
    if marked >> (8 * length + 2):
        raise DecodeError("range", f"its value is too large for {length} bytes: a letter was misread or changed")
    if (marked >> half) & 3 != MARKER:
        raise DecodeError("marker", "its marker is not Sigil's: a string of another format, or a changed letter")
    d = (marked >> (half + 2)) << half | (marked & ((1 << half) - 1))
    return d.to_bytes(length, "big")


def decode_readings(readings, length):
    """The data of `length` bytes that one reading decodes to, for a reader
    unsure of some letters (an OCR tool, say): `readings` gives each letter's
    possible readings, one string a letter, the likeliest first. Raises
    DecodeError "ambiguous" when several readings decode to different data,
    and the first reading's error when none decodes. The work is the
    product of the readings' counts."""
    import itertools
    if any(not r for r in readings):  # a letter with no reading: the text is a letter short
        return decode("".join(r[0] for r in readings if r), length)
    found, first_error = [], None
    for choice in itertools.product(*readings):
        try:
            data = decode("".join(choice), length)
        except DecodeError as e:
            first_error = first_error or e
            continue
        if data not in found:
            found.append(data)
    if len(found) > 1:
        raise DecodeError("ambiguous", f"{len(found)} readings decode, to different data")
    if not found:
        raise first_error
    return found[0]
