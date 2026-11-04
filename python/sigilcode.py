"""Sigil: bytes of a known length written as a sigil, one word that a
double-click selects whole, of letters with no two alike, and a check that
confirms a reading or picks the right one of several. A sigil has one of two
forms: handled, which begins with the value's first 7 hex digits, and plain,
all letters.

    encode(data, handle=True) -> str              # the sigil, handled or plain
    decode(sigil, length) -> bytes                # either form; or raises DecodeError
    decode_readings(readings, length) -> bytes    # the one reading that decodes

This is the reference implementation; the specification is README.md ("The
encoding"). Base N = 2,048, 11 bits a letter; K is a prime larger than N.

- Handled: U+200E LEFT-TO-RIGHT MARK, the handle (the data's first 28 bits
  as 7 lowercase hex digits), and n = ceil((8 * length - 14) / 11) letters.
  The letters write t = m * K + r: m is the rest of the data with the marker
  bits 01 between its high and low halves, and r < K the number that makes
  the whole word, read as handle * N^n + t, a multiple of K.
- Plain: n = ceil((8 * length + 14) / 11) letters writing m * K, m the whole
  data with the marker bits 01 between its halves.

A decoder tells the forms apart by the first character (hex digits are no
letters), checks the multiple of K, which catches every changed character
and every swap of characters one or two apart, and checks that the marker
is 01. Decoding skips the characters of skipped.txt (white space, the mark,
and four invisible characters copying inserts), reads the handle's hex in
either case, and refuses everything else outside the handle's digits and
the alphabet.

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
MARK = "\u200e"
HANDLE = 7  # hex digits, 28 bits
HEX = {c: int(c, 16) for c in "0123456789abcdefABCDEF"}


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


def layout(length, handle=True):
    """(n, K) for data of `length` bytes (at least 8) in the handled or the
    plain form: the sigil's letters, the fewest whose room 2^(11n - bits - 2)
    holds a prime larger than N (2,053 or more), and K, check_prime(room).
    The letters carry bits = 8 * length - 28 of the data handled, all
    8 * length plain."""
    assert length >= 8, "Sigil encodes at least 8 bytes"
    rest = 8 * length - (4 * HANDLE if handle else 0)
    n = -(-(rest + 14) // 11)
    room = 1 << (11 * n - rest - 2)
    if room not in CHECK_PRIMES:
        CHECK_PRIMES[room] = check_prime(room)
    return n, CHECK_PRIMES[room]


def marked(rest, bits, marker):
    """`rest`, of `bits` bits, with `marker` between its high and low halves."""
    half = bits // 2
    return (((rest >> half) << 2 | marker) << half) | (rest & ((1 << half) - 1))


def offset(handle, n, k):
    """r: the number below K that makes handle * N^n + m * K + r a multiple of K."""
    return -handle * pow(N, n, k) % k


def letters(t, n):
    """The n letters that write t."""
    return "".join(ALPHABET[(t >> 11 * i) & 2047] for i in reversed(range(n)))


def word(handle, t, n):
    """The handled sigil of a handle and the letters' value t."""
    return MARK + f"{handle:07x}" + letters(t, n)


def encode(data: bytes, handle=True) -> str:
    """`data`'s sigil: handled, the mark, the handle, and
    layout(len(data))[0] letters of the alphabet; or plain,
    layout(len(data), False)[0] letters. Its protection against look-alikes
    holds for data that looks random (a secure hash's output, a key, a random
    identifier): hash or jumble structured data before encoding it
    (README.md, "Data with structure")."""
    n, k = layout(len(data), handle)
    d = int.from_bytes(data, "big")
    if not handle:
        return letters(marked(d, 8 * len(data), MARKER) * k, n)
    bits = 8 * len(data) - 4 * HANDLE
    top = d >> bits
    return word(top, marked(d & ((1 << bits) - 1), bits, MARKER) * k + offset(top, n, k), n)


def skipped(ch):
    return any(a <= ord(ch) <= b for a, b in SKIPPED)


def decode(sigil: str, length: int) -> bytes:
    """The `length` bytes `sigil` encodes; the characters of skipped.txt in
    it are skipped."""
    chars = [(i, ch) for i, ch in enumerate(sigil) if not skipped(ch)]
    # The form, by the first character: hex digits are no letters.
    handled = bool(chars) and chars[0][1] in HEX
    n, k = layout(length, handled)
    h = HANDLE if handled else 0
    if len(chars) != h + n:
        raise DecodeError("length", f"{len(chars)} characters; {length} bytes take {h + n}"
                          f"{' with the handle' if handled else ''}")
    handle = t = 0
    for j, (i, ch) in enumerate(chars):
        if j < h and ch not in HEX:
            raise DecodeError("character", f"character {i + 1} (U+{ord(ch):04X}) is not a hex digit of the handle")
        if j >= h and ch not in DIGIT:
            raise DecodeError("character", f"character {i + 1} (U+{ord(ch):04X}) is not a letter of the alphabet")
        if j < h:
            handle = handle << 4 | HEX[ch]
        else:
            t = t << 11 | DIGIT[ch]
    if (handle * pow(N, n, k) + t) % k:
        raise DecodeError("check", "the check fails: a character was misread or changed")
    m, bits = t // k, 8 * length - 4 * h
    half = bits // 2
    if m >> (bits + 2):
        raise DecodeError("range", f"its value is too large for {length} bytes: a letter was misread or changed")
    if (m >> half) & 3 != MARKER:
        raise DecodeError("marker", "its marker is not Sigil's: a string of another format, or a changed letter")
    rest = (m >> (half + 2)) << half | (m & ((1 << half) - 1))
    return (handle << bits | rest).to_bytes(length, "big")


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
