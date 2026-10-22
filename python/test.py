"""The reference implementation against vectors.json, BLAKE3's official test
vectors, and the claims of README.md.

    python3 python/test.py [BLAKE3_TEST_VECTORS_JSON]

The BLAKE3 vectors are test_vectors/test_vectors.json in github.com/BLAKE3-team/BLAKE3;
without the argument, the BLAKE3 checks use the two hashes README.md quotes.
"""
import hashlib
import json
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
    # BLAKE3, which the check uses.
    assert B.blake3_hash(b"").hex() == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
    if len(sys.argv) > 1:
        tv = json.loads(Path(sys.argv[1]).read_text())
        for c in tv["cases"]:
            data = bytes(i % 251 for i in range(c["input_len"]))
            assert B.blake3_hash(data, len(c["hash"]) // 2).hex() == c["hash"], c["input_len"]
            assert B.blake3_derive_key(tv["context_string"], data, len(c["derive_key"]) // 2).hex() == c["derive_key"]
        print(f"BLAKE3: {len(tv['cases'])} official vectors agree, hashing and deriving keys")

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

    assert B.layout(32) == (26, 14)
    print("layouts (characters, check bits):", {length: B.layout(length) for length in (1, 8, 16, 20, 32, 48, 64)})

    # Readings: one character read three ways (the right one among them), and
    # one character unread (every character a candidate).
    import random
    rng = random.Random(1)
    three = unread = 0
    for i in range(200):
        data = hashlib.sha256(b"readings" + i.to_bytes(2, "big")).digest()
        sigil = B.encode(data)
        j = rng.randrange(len(sigil))
        guesses = [sigil[j]] + rng.sample([c for c in B.ALPHABET if c != sigil[j]], 2)
        rng.shuffle(guesses)
        readings = [c for c in sigil]
        readings[j] = "".join(guesses)
        three += B.decode_readings(readings, 32) == [data]
        if i < 40:
            readings[j] = B.ALPHABET
            unread += B.decode_readings(readings, 32) == [data]
    print(f"one character read three ways: the right data alone in {three} of 200; "
          f"one character unread: alone in {unread} of 40")

if __name__ == "__main__":
    main()
