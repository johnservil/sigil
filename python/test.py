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

    assert B.LEAST_K == 1361 and B.layout(32) == (26, 22381)
    for length in range(1, 1025):
        n, k = B.layout(length)
        assert B.N < k and B.is_prime(k) and k << 8 * length <= B.N ** n and B.N ** (n - 1) < B.LEAST_K << 8 * length, length
    print("layouts (characters, K):", {length: B.layout(length) for length in (1, 8, 16, 20, 32, 48, 64)},
          "; at every length to 1024 bytes K is a prime above N and n the fewest characters that hold one")

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
                    assert error(sigil[:j] + c + sigil[j + 1:], 32) in ("range", "check")
                    changed += 1
            for gap in (1, 2):
                if j + gap < len(sigil) and sigil[j] != sigil[j + gap]:
                    t = list(sigil)
                    t[j], t[j + gap] = t[j + gap], t[j]
                    assert error("".join(t), 32) in ("range", "check")
                    swapped += 1
        j = rng.randrange(len(sigil))
        readings = list(sigil)
        readings[j] = B.ALPHABET
        assert B.decode_readings(readings, 32) == [data]
        recovered += 1
    print(f"every one of {changed} changed characters and {swapped} swaps of characters one or two apart fails to decode; "
          f"one unread character comes back alone in {recovered} of {recovered}")

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
        assert B.decode_readings(readings, 32) == [data]
        three += 1
    print(f"one character read three ways: the right data alone in {three} of 200")


if __name__ == "__main__":
    main()
