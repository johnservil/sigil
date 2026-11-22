# Checking Sigil for yourself

This directory holds the format as Lean definitions (`Sigil/Spec.lean`) and
a proof of the layout's contract (`Sigil/Layout.lean`): for every length, K
is a prime above the alphabet's size that fits beside the marked bits, in
the fewest letters. They use Lean 4.31.0 and its core library, with no
Mathlib or external solver.

**Not proved for 0.2 yet.** For 0.1's format this directory also proved
that the decoder inverts the encoder, that the check catches every changed
letter and every swap of letters one or two apart, and eleven known
answers. Those files are at the tag
`v0.1.2+5404f5e7b0912b58eb7d34006c7fb5c73cd4ecc7`. In 0.2's format a handle
of hex digits takes part in the check, and 0.2 is a release on trial: its
proofs wait until the format settles. Until then those properties are
tested, not proved ([QUALITY.md](../QUALITY.md)).

The optimized Rust implementation has tests, **but its correctness and its
executable bytes have no proof**. Compiling Lean likewise leaves its
compiler and runtime in the trust chain.

## Check an answer for your own input

From the repository root:

```sh
(cd lean && lake build)
python3 tools/certificate.py encode 0000000000000000 > /tmp/Answer.lean
cat /tmp/Answer.lean
(cd lean && lake env lean --trust=0 /tmp/Answer.lean)
```

The generated statement is:

```lean
theorem answer :
    Sigil.encode ([0, 0, 0, 0, 0, 0, 0, 0] : List UInt8) =
    ([8206, 48, 48, 48, 48, 48, 48, 48, 48, 2308, 2323, 43811, 11668, 2308] : List Nat) := by decide +kernel
```

The input is eight zero bytes, the shortest data Sigil encodes. The output
is the left-to-right mark (8,206), the handle `00000000` (48 eight times)
and five letters, `ऄओꬣⶔऄ`, which you can calculate by hand. After the
handle's 32 bits the other 32 are zero. With the marker bits `01` between
their two halves they are 65,536; times K = 2,096,881 that is
137,421,193,216, and a zero handle adds nothing to it. In base 2,048 that
is 0, 15, 2,043, 1,568 and 0: letters of the alphabet with code points
2,308, 2,323, 43,811, 11,668 and 2,308. Both input and output are explicit
numerals, in stored order. A 32-byte input is supplied as 64 hex digits to
the same command.

To check a decoding, including its exact error:

```sh
python3 tools/certificate.py decode 8 '00000000ऄओꬣⶔऄ' > /tmp/Answer.lean
# Statement: Sigil.decode [48, 48, 48, 48, 48, 48, 48, 48, 2308, 2323, 43811, 11668, 2308] 8 = .ok [0, 0, 0, 0, 0, 0, 0, 0]
python3 tools/certificate.py decode 8 '00000000ऄओꬣⶔअ' > /tmp/Error.lean
# Statement: Sigil.decode [48, 48, 48, 48, 48, 48, 48, 48, 2308, 2323, 43811, 11668, 2309] 8 = .error (.check)
(cd lean && lake env lean --trust=0 /tmp/Answer.lean)
(cd lean && lake env lean --trust=0 /tmp/Error.lean)
```

`certificate.py` uses the Python reference to **propose** the result.
`decide +kernel` checks it by reducing the Lean specification; it uses no
`native_decide` or compiled computation as a proof. `--trust=0` also checks
imported declarations. Kernel evaluation can be much more expensive than
running the compiled implementation. Use it for checking particular answers;
use the compiled implementation for bulk encoding.

**Inspect the statement before accepting it.** A malicious generator could
state the right answer to the wrong question. Confirm the input bytes or
code points and the byte length, and treat the output literals in that
statement as the answer. A displayed glyph, a terminal, or another program
can misrepresent those literals. The checker passing does not certify text
printed elsewhere.

The file prints the theorem's axioms. The certificates tested here use
none, or `propext`. Inspect the actual list for your certificate. A failed
check, a warning about `sorry`, or an unexpected axiom leaves the answer
unverified. The generator is small and editable: Bob can write the literal
statement himself.

## The vectors and the rejection tests

```sh
(cd lean && lake exe tests ../vectors.tsv)
python3 tools/test_certificate.py
```

These are two distinct checks:

- `Tests.lean` runs all 1,554 shared vectors through **compiled** Lean.
  This is integration evidence, alongside the Python, TypeScript and Rust
  tests. It is not 1,554 kernel proofs.
- `test_certificate.py` checks generated certificates through Lean with
  `--trust=0`, then deliberately changes an output code point, a decoded
  byte and an error kind. Every corrupted statement must be rejected. It
  also checks that input text enters generated source only as numerals.

A finite test corpus cannot exclude a malicious rare case.

## Proof coverage and reliances

[What Bob can verify about Sigil](../VERIFICATION.md) holds the property
checklist, current proof coverage, reliance matrices and executable-proof
goal. It distinguishes specification proofs, implementation proofs and
assurance about the executable Bob runs.

After `lake build`, run this from `lean/` to recheck the imported proof and
inspect its statement and axiom list:

```sh
lake env lean --trust=0 Audit.lean
```

The expected axiom list is a subset of Lean's standard `propext`,
`Classical.choice` and `Quot.sound`.
