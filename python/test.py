"""The reference implementation against vectors.json and the claims of
README.md.

    python3 python/test.py
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sigilcode as B

ROOT = Path(__file__).resolve().parent.parent


def error(text, length):
    try:
        B.decode(text, length)
        return None
    except B.DecodeError as e:
        return e.kind


def main():
    v = json.loads((ROOT / "vectors.json").read_text(encoding="utf-8"))
    for g in v["good"]:
        data = bytes.fromhex(g["data"])
        assert B.encode(data) == g["text"] and B.decode(g["text"], len(data)) == data, g
    for g in v["variants"]:
        data = bytes.fromhex(g["data"])
        assert B.decode(g["text"], len(data)) == data, g
    for b in v["bad"]:
        assert error(b["text"], b["length"]) == b["error"], b
    print(f"vectors: {len(v['good'])} good, {len(v['variants'])} variants and {len(v['bad'])} bad agree")

    assert B.layout(32) == (25, 131063) and B.layout(16) == (13, 8179) and B.layout(8) == (8, 4193633)
    assert [B.check_prime(1 << e) for e in range(12, 23)] == [4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633]
    for length in range(1, 1025):
        n, k = B.layout(length)
        room = 1 << (11 * n - 8 * length - 2)
        assert B.N < k <= room and B.is_prime(k) and (room >> 11) < 2053, length
    print("layouts (letters, K):", {length: B.layout(length) for length in (1, 8, 10, 16, 20, 24, 32, 64)},
          "; at every length to 1024 bytes n is the fewest letters whose room holds a prime above N")
    # Every letter is three bytes of UTF-8, and none is a hex digit.
    assert all(len(c.encode()) == 3 for c in B.ALPHABET) and not set(B.ALPHABET) & set("0123456789abcdefABCDEF")

    # The guarantees, on 256-bit values: every changed character and every
    # swap of characters one or two apart fails to decode, and one unread
    # character comes back.
    rng = random.Random(1)
    changed = swapped = recovered = 0
    for i in range(20):
        data = hashlib.sha256(b"guarantees" + bytes([i])).digest()
        sigil = B.encode(data)
        for j in range(len(sigil)):
            for c in B.ALPHABET:
                if c != sigil[j]:
                    assert error(sigil[:j] + c + sigil[j + 1:], 32) == "check"
                    changed += 1
            for gap in (1, 2):
                if j + gap < len(sigil) and sigil[j] != sigil[j + gap]:
                    t = list(sigil)
                    t[j], t[j + gap] = t[j + gap], t[j]
                    assert error("".join(t), 32) == "check"
                    swapped += 1
        j = rng.randrange(len(sigil))
        readings = list(sigil)
        readings[j] = B.ALPHABET
        assert B.decode_readings(readings, 32) == data
        recovered += 1
    print(f"every one of {changed} changed letters and {swapped} swaps of letters one or two apart fails the check; "
          f"one unread letter comes back alone in {recovered} of {recovered}")

    # Readings: one character read three ways, the right one among them.
    three = 0
    for i in range(200):
        data = hashlib.sha256(b"readings" + i.to_bytes(2, "big")).digest()
        sigil = B.encode(data)
        j = rng.randrange(len(sigil))
        guesses = [sigil[j]] + rng.sample([c for c in B.ALPHABET if c != sigil[j]], 2)
        rng.shuffle(guesses)
        readings = list(sigil)
        readings[j] = "".join(guesses)
        assert B.decode_readings(readings, 32) == data
        three += 1
    print(f"one letter read three ways: the right data alone in {three} of 200")
    # The marker in the middle leaves both edges free: over random 256-bit data,
    # the first and the last letter each take more than 1,900 of the 2,048 values.
    firsts, lasts = set(), set()
    for i in range(20000):
        sigil = B.encode(hashlib.sha256(b"edges" + i.to_bytes(4, "big")).digest())
        firsts.add(sigil[0]); lasts.add(sigil[-1])
    assert len(firsts) > 1900 and len(lasts) > 1900, (len(firsts), len(lasts))
    print(f"the first letter took {len(firsts)} and the last {len(lasts)} of the 2,048 values over 20,000 random 256-bit sigils")


if __name__ == "__main__":
    main()
