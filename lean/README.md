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

## What has a universal proof?

| Claim | Status |
|---|---|
| The alphabet ascends strictly and none of its entries is ignored | Kernel-checked facts |
| Every alphabet entry reads as its digit | Proved |
| The layout's K exceeds N and K·2^(8L) fits in N^n | Proved (`N_lt_K`, `K_fits`) |
| Bytes and base-N digits round-trip | Proved |
| Decoding an encoding returns the original data, for every byte list | Proved (`decode_encode`) |
| K is mathematically prime, maximal, and the character count minimal | Proved for every byte length (`isPrime_iff`, `layout_contract`) |
| Canonical alphabet digits decode by exactly the range/remainder checks | Proved (`decode_alphabet_digits`) |
| All accepted representations and exact failures match an independent format characterization | Full characterization including case variants and ignored characters remains |
| Single-digit-error detection | Proved arithmetically and for the Lean decoder on canonical alphabet text (`single_change_decode_rejected`) |
| Adjacent and two-apart swaps; uniqueness of one erased digit | Proved for the AN code (`adjacent_swap_detected`, `two_apart_swap_detected`, `erased_digit_unique`); `decode_nonmultiple` connects failed divisibility to decoder rejection |
| `decode_readings` enumerates all and only valid readings | Tests; specification and proof remain |
| Optimized Rust matches the specification, including failures and termination | Tests; refinement proof remains |
| The executable Bob runs matches the specification | Open |
| Work, allocation and platform bounds | Full contracts and proofs remain |

After `lake build`, run `lake env lean --trust=0 Audit.lean` from this
directory to recheck imported proofs and inspect the main theorem statements
and axiom lists.

The proofs use only Lean's standard axioms (`propext`, `Classical.choice`,
`Quot.sound`), with no `sorry` or `native_decide`. `Sigil.Prime` states
mathematical primality explicitly: at least two, with only one and itself
as natural-number divisors. `isPrime_iff` connects that definition to the
trial-division program; `layout_contract` states all the layout guarantees
together. The error-control theorems quantify over every position and digit
value. Erasure uniqueness is a property of digits; uppercase spellings of
the same digit are aliases, not different recovered data.
The Lean definitions also have a value for an empty byte list; the public
implementations require at least one byte.

The look-alike attack estimates in the main README also need a separate
security analysis: valid sigils have restricted and dependent digits, and
the first digit is not uniform over the alphabet. The figures of 10.4 bits
per compared character and 83 bits for eight characters are approximate
capacity estimates, not proved work factors. Jumbling a structured input
likewise needs a security argument for that input's validity constraints.

## The trust boundary, and the executable proof still to build

For a kernel-checked answer Bob trusts:

1. His reviewed format definitions and alphabet data.
2. Lean's kernel binary, its foundational rules and the axioms
   used. Independent kernels can reduce dependence on a single checker.
3. The correspondence between his intended input, the theorem's literals,
   and the answer he uses, plus the hardware and operating system running
   the check.

Rebuilding modules from reviewed source is useful for tying definitions to
source; `--trust=0` checks imported declarations but cannot decide whether
they describe Bob's intended format. Reproducible builds establish agreement,
not freedom from a compiler backdoor. Diverse double compilation is a
separate way to investigate a compiler's correspondence to its source.

For the fast executable, the goal is a proof certificate about **Bob's own
build's machine-code bytes**. The checker must connect those bytes, entry
points and machine semantics to the format and its resource contract. The
coverage must include reachable helpers and any runtime or external calls;
a command-line tool also needs its input parsing, output and exit status
covered. A proof of an isolated encoding function would leave those gaps.

An Aeneas experiment in a scratch crate has translated a carry-propagating
Rust multiply-add loop into Lean and built it against the Aeneas library.
That is feasibility evidence, not a proof of Sigil's Rust. A source-level
refinement proof can help develop the arithmetic invariants, but leaves
extraction, compilation and linking outside its claim. It becomes part of
the executable assurance only when those steps are independently checked
or replaced by a direct proof about the resulting bytes.
