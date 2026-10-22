"""The reference implementation against vectors.json and against the claims
of README.md.

    python3 python/test.py
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import base1160 as B

ROOT = Path(__file__).resolve().parent.parent


def errors(text, length):
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
    for g in v["spaced"]:
        data = bytes.fromhex(g["data"])
        assert B.decode(g["text"], len(data)) == data, g
    for b in v["bad"]:
        assert errors(b["text"], b["length"]) == b["error"], b
    print(f"vectors: {len(v['good'])} good, {len(v['spaced'])} spaced and {len(v['bad'])} bad agree")

    n, k = B.layout(32)
    assert (n, k) == (27, 474983)
    print("layouts:", {length: B.layout(length) for length in (16, 20, 32, 48, 64)})

    rng = random.Random(1)
    caught = 0
    for i in range(2):
        text = B.encode(hashlib.sha256(bytes([i])).digest())
        for j in range(n):
            for c in B.ALPHABET:
                if c != text[j]:
                    assert errors(text[:j] + c + text[j + 1:], 32) == "corrupt"
                    caught += 1
    print(f"every single substitution of two 32-byte values caught: {caught:,}")

    swaps = 0
    for i in range(1000):
        text = B.encode(hashlib.sha256(i.to_bytes(4, "big")).digest())
        for j in range(n - 1):
            if text[j] != text[j + 1]:
                assert errors(text[:j] + text[j + 1] + text[j] + text[j + 2:], 32) == "corrupt"
                swaps += 1
    print(f"every swap of neighbours in 1,000 values caught: {swaps:,}")

    text = B.encode(bytes(32))
    assert all(errors(text[:j], 32) == "length" for j in range(n))
    print("every truncation caught")

    tries, passed = 1_000_000, 0
    for _ in range(tries):
        if errors("".join(rng.choice(B.ALPHABET) for _ in range(n)), 32) is None:
            passed += 1
    expect = tries * 2 ** 256 / B.N ** n
    print(f"random {n}-character texts that decode: {passed} of {tries:,} (expected {expect:.1f}: 2^256 / N^{n})")


if __name__ == "__main__":
    main()
