# Checking Sigil for yourself

This directory contains the mathematical format (`Sigil/Spec.lean`), a proof
that its decoder inverts its encoder (`Sigil/Theorems.lean`), the layout's
prime/maximality/minimality proofs (`Sigil/Layout.lean`), error-control
proofs (`Sigil/Errors.lean`), and fixed known answers checked by Lean's kernel
(`Sigil/KnownAnswers.lean`). They use
Lean 4.31.0 and its core library, with no Mathlib or external solver.

The optimized Rust implementation has tests, **but its correctness and its
executable bytes have no proof yet**. The specification's round-trip theorem
covers the Lean definitions alone. Compiling Lean likewise leaves
its compiler and runtime in the trust chain.

## Check an answer for your own input

From the repository root:

```sh
(cd lean && lake build)
python3 tools/certificate.py encode 00 > /tmp/Answer.lean
cat /tmp/Answer.lean
(cd lean && lake env lean --trust=0 /tmp/Answer.lean)
```

The generated statement is:

```lean
theorem answer :
    Sigil.encode ([0] : List UInt8) =
    ([48, 48] : List Nat) := by decide +kernel
```

The input is one zero byte. The output is two U+0030 characters, `00`:
0 multiplied by K is still 0, written as two zero digits. Both input and
output are explicit numerals, in stored order. A 32-byte input is supplied
as 64 hex digits to the same command.

To check a decoding, including its exact error:

```sh
python3 tools/certificate.py decode 1 '00' > /tmp/Answer.lean
# Statement: Sigil.decode [48, 48] 1 = .ok [0]
python3 tools/certificate.py decode 1 '01' > /tmp/Error.lean
# Statement: Sigil.decode [48, 49] 1 = .error (.check)
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

The file prints the theorem's axioms. Encoding certificates here use none;
the decoding certificates tested here use `propext`. Inspect the actual
list for your certificate. A failed check, a warning about `sorry`, or an
unexpected axiom leaves the answer unverified. The generator is small and
editable: Bob can write the literal statement himself.

## Known answers and rejection tests

```sh
(cd lean && lake build Sigil.KnownAnswers)
(cd lean && lake exe tests ../vectors.tsv)
python3 tools/test_certificate.py
```

These are three distinct checks:

- `KnownAnswers.lean` fixes literal encodings (zero, maximum byte, leading
  zero and a 32-byte sequence), a successful decoding, uppercase and ignored
  characters, and all four exact error kinds. The kernel checks each one.
  The Python reference proposed the nontrivial answers; these are format
  fixtures, not an independently designed specification.
- `Tests.lean` runs all 1,100 shared vectors through **compiled** Lean.
  This is integration evidence, alongside the Python, TypeScript and Rust
  tests. It is not 1,100 kernel proofs.
- `test_certificate.py` checks generated certificates through Lean with
  `--trust=0`, then deliberately changes an output code point, a decoded
  byte and an error kind. Every corrupted statement must be rejected. It
  also checks that input text enters generated source only as numerals.

Known answers catch misunderstandings of the format that a round-trip
alone can miss. A finite test corpus cannot exclude a malicious rare case.

## Proof coverage and reliances

[What Bob can verify about Sigil](../VERIFICATION.md) holds the property
checklist, current proof coverage, reliance matrices and executable-proof
goal. It distinguishes specification proofs, implementation proofs and
assurance about the executable Bob runs.

After `lake build`, run this from `lean/` to recheck imported proofs and
inspect the main theorem statements and axiom lists:

```sh
lake env lean --trust=0 Audit.lean
```

Expected axiom lists are subsets of Lean's standard `propext`,
`Classical.choice` and `Quot.sound`.
