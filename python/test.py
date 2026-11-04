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
        assert B.encode(data, g["form"] == "handled") == g["text"] and B.decode(g["text"], len(data)) == data, g
    for g in v["variants"]:
        data = bytes.fromhex(g["data"])
        assert B.decode(g["text"], len(data)) == data, g
    for b in v["bad"]:
        assert error(b["text"], b["length"]) == b["error"], b
    print(f"vectors: {len(v['good'])} good, {len(v['variants'])} variants and {len(v['bad'])} bad agree")

    assert B.layout(32) == (22, 4093) and B.layout(16) == (11, 524269) and B.layout(8) == (5, 131063)
    assert B.layout(32, False) == (25, 131063) and B.layout(16, False) == (13, 8179) and B.layout(8, False) == (8, 4193633)
    assert [B.check_prime(1 << e) for e in range(12, 23)] == [4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633]
    for handled in (True, False):
        for length in range(8, 1025):
            n, k = B.layout(length, handled)
            room = 1 << (11 * n - (8 * length - (28 if handled else 0)) - 2)
            assert B.N < k <= room and B.is_prime(k) and (room >> 11) < 2053, length
        print(f"layouts {'handled' if handled else 'plain'} (letters, K):",
              {length: B.layout(length, handled) for length in (8, 16, 20, 32, 64)})
        # A random string of the right characters decodes once in
        # 2^(handle bits + 11n - 8L): the data's 2^(8L) words among them all.
        print("  a random string decodes once in", {length: f"2^{(28 if handled else 0) + 11 * B.layout(length, handled)[0] - 8 * length}"
                                                  for length in (8, 16, 20, 24, 32, 48, 64)})
    print("  at every length to 1024 bytes n is the fewest letters whose room holds a prime above N")
    # Every letter is three bytes of UTF-8, and none is a hex digit.
    assert all(len(c.encode()) == 3 for c in B.ALPHABET) and not set(B.ALPHABET) & set("0123456789abcdefABCDEF")

    # D3: the handle is the data's hex, its first 7 digits; R2: every sigil of
    # a length is the same size however it is counted; D12: sigils sort as
    # their values do, by code point, UTF-8 and UTF-16.
    for length, handled in [(length, handled) for length in (8, 20, 32, 64) for handled in (True, False)]:
        datas = [hashlib.sha256(b"order" + bytes([length]) + i.to_bytes(2, "big")).digest() * 2 for i in range(300)]
        datas = [d[:length] for d in datas] + [bytes(length), b"\xff" * length]
        words = [B.encode(d, handled) for d in datas]
        if handled:
            assert all(w[0] == B.MARK and w[1:1 + B.HANDLE] == d.hex()[:B.HANDLE] for w, d in zip(words, datas))
        sizes = {(len(w), len(w.encode()), len(w.encode("utf-16-le"))) for w in words}
        assert len(sizes) == 1, sizes
        by_value = [w for _, w in sorted(zip(datas, words))]
        assert sorted(words) == by_value and sorted(words, key=lambda w: w.encode()) == by_value
        assert sorted(words, key=lambda w: w.encode("utf-16-be")) == by_value
    print("the handle is the data's first 7 hex digits; every sigil of a length is one size; sigils sort as their values")

    # The guarantees, on 256-bit values: every changed character (a hex digit
    # for a hex digit, a letter for a letter) and every swap of characters one
    # or two apart fails the check (a swap across the handle's end puts a
    # letter among its digits, which decoding refuses), and one unread
    # character comes back.
    rng = random.Random(1)
    changed = swapped = recovered = 0
    for i in range(20):
        handled = i % 2 == 0
        start = 1 + B.HANDLE if handled else 0
        data = hashlib.sha256(b"guarantees" + bytes([i])).digest()
        sigil = B.encode(data, handled)
        for j in range(1 if handled else 0, len(sigil)):
            for c in ("0123456789abcdef" if j < start else B.ALPHABET):
                if c != sigil[j]:
                    assert error(sigil[:j] + c + sigil[j + 1:], 32) == "check"
                    changed += 1
            for gap in (1, 2):
                if j + gap < len(sigil) and sigil[j] != sigil[j + gap]:
                    t = list(sigil)
                    t[j], t[j + gap] = t[j + gap], t[j]
                    across = (j < start) != (j + gap < start)
                    assert error("".join(t), 32) == ("character" if across else "check")
                    swapped += 1
        unread = [(rng.randrange(start, len(sigil)), B.ALPHABET)] + ([(rng.randrange(1, start), "0123456789abcdef")] if handled else [])
        for j, choices in unread:
            readings = list(sigil)
            readings[j] = choices
            assert B.decode_readings(readings, 32) == data
            recovered += 1
    print(f"every one of {changed} changed characters and {swapped} swaps of characters one or two apart fails to decode; "
          f"one unread letter or hex digit comes back alone in {recovered} of {recovered}")

    # Readings: one character read three ways, the right one among them.
    three = 0
    for i in range(200):
        data = hashlib.sha256(b"readings" + i.to_bytes(2, "big")).digest()
        sigil = B.encode(data)
        j = rng.randrange(1 + B.HANDLE, len(sigil))
        guesses = [sigil[j]] + rng.sample([c for c in B.ALPHABET if c != sigil[j]], 2)
        rng.shuffle(guesses)
        readings = list(sigil)
        readings[j] = "".join(guesses)
        assert B.decode_readings(readings, 32) == data
        three += 1
    print(f"one letter read three ways: the right data alone in {three} of 200")
    # D8: the marker in the middle leaves both edges of the letters free: over
    # random 256-bit data, the first letter after the handle and the last each
    # take more than 1,900 of the 2,048 values.
    firsts, lasts = set(), set()
    for i in range(20000):
        sigil = B.encode(hashlib.sha256(b"edges" + i.to_bytes(4, "big")).digest())
        firsts.add(sigil[1 + B.HANDLE]); lasts.add(sigil[-1])
    assert len(firsts) > 1900 and len(lasts) > 1900, (len(firsts), len(lasts))
    print(f"the first letter took {len(firsts)} and the last {len(lasts)} of the 2,048 values over 20,000 random 256-bit sigils")


if __name__ == "__main__":
    main()
