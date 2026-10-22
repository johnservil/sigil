#!/usr/bin/env python3
"""Propose an answer as a Lean theorem with explicit input and output literals.

    python3 tools/certificate.py encode HEX > /tmp/Answer.lean
    python3 tools/certificate.py decode LENGTH TEXT > /tmp/Answer.lean
    (cd lean && lake env lean --trust=0 /tmp/Answer.lean)

The Python reference proposes an answer. Lean's kernel computes the specification
and checks it, without native_decide. Inspect the theorem's input and output:
a generator can lie about which question it asked, even when its theorem checks.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import sigilcode as S

HEADER = """import Sigil.Spec

-- Input and output below are byte/code-point literals, in stored order.
-- Check that these are your intended input and output before checking the proof.
-- Run from lean/: lake env lean --trust=0 /absolute/path/to/Answer.lean
set_option maxRecDepth 100000
set_option maxHeartbeats 10000000

namespace SigilAnswer
-- Equality is decidable for both successful results and exact errors.
deriving instance DecidableEq for Except

"""


def nats(values):
    """Lean numerals only: no input text enters the source as executable text."""
    return "[" + ", ".join(str(x) for x in values) + "]"


def encoding(data):
    assert data, "Sigil encodes at least one byte"
    answer = S.encode(data)
    return (HEADER +
            f"theorem answer :\n"
            f"    Sigil.encode ({nats(data)} : List UInt8) =\n"
            f"    ({nats(map(ord, answer))} : List Nat) := by decide +kernel\n\n"
            "#print axioms answer\nend SigilAnswer\n")


def decoding(text, length):
    assert length >= 1, "Sigil encodes at least one byte"
    points = list(map(ord, text))
    n, _ = S.layout(length)
    kept = [(i, ch) for i, ch in enumerate(text, 1) if not S.ignored(ch)]
    try:
        data = S.decode(text, length)
        expected = f".ok {nats(data)}"
    except S.DecodeError as e:
        if e.kind == "length":
            error = f".length {len(kept)} {n}"
        elif e.kind == "character":
            position, ch = next((i, ch) for i, ch in kept if ch not in S.DIGIT)
            error = f".character {position} {ord(ch)}"
        else:
            assert e.kind in ("range", "check"), "unknown decoding error"
            error = f".{e.kind}"
        expected = f".error ({error})"
    return (HEADER +
            f"theorem answer :\n"
            f"    Sigil.decode {nats(points)} {length} =\n"
            f"    {expected} := by decide +kernel\n\n"
            "#print axioms answer\nend SigilAnswer\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    enc = sub.add_parser("encode", help="propose a theorem for input bytes in hex")
    enc.add_argument("hex")
    dec = sub.add_parser("decode", help="propose a theorem for text and its expected byte length")
    dec.add_argument("length", type=int)
    dec.add_argument("text")
    args = p.parse_args()
    if args.operation == "encode":
        print(encoding(bytes.fromhex(args.hex)), end="")
    else:
        print(decoding(args.text, args.length), end="")


if __name__ == "__main__":
    main()
