# What Bob can verify about Sigil

Bob is a skeptical user who wants to establish that the version he runs is
safe, including against an enemy who plants a bug triggered by one particular
input. He can choose both the properties he demands and the components he
relies on to establish them.

This page records the properties, current evidence, possible verification
paths, and their remaining reliances. [The Lean guide](lean/README.md)
explains how to check proofs and particular answers today.

## Properties Bob might want to establish

**Proved** below means a theorem about the Lean definitions within the stated
scope. The optimized Rust and its executable bytes still have tests; their
correctness proofs remain open.

| Property | Current evidence and scope |
|---|---|
| The specification describes Bob's intended format | Readable definitions and known answers; Bob's review remains essential |
| The alphabet follows the documented Unicode rules | Deterministic generator and checks; the rules-to-alphabet connection has no formal proof |
| Alphabet entries are distinct and never ignored | Kernel-checked facts: strict ascending order and absence from the ignored ranges |
| Every alphabet entry reads as its prescribed digit | Proved for canonical alphabet entries |
| Layout chooses a prime K above N, with sufficient capacity | Proved for every byte length (`layout_contract`) |
| K is the largest prime that fits, and the character count is minimal | Proved for every byte length (`isPrime_iff`, `layout_contract`) |
| Bytes and base-N digits convert back and forth | Proved |
| Encoding preserves all input bytes | Lean's decoder inverts its encoder (`decode_encode`) |
| Every permitted spelling is accepted | Canonical digits proved; uppercase and ignored-character variants tested |
| Every forbidden spelling receives the prescribed error | Canonical range/remainder checks proved (`decode_alphabet_digits`); full parsing and error characterization remains |
| Every single-digit substitution is detected | Proved for the AN code and for the Lean decoder on canonical alphabet text (`single_change_decode_rejected`) |
| Every swap of unequal neighbours or digits two apart is detected | Proved for the AN code (`adjacent_swap_detected`, `two_apart_swap_detected`); `decode_nonmultiple` connects failed divisibility to decoder rejection |
| One erased digit has a unique valid replacement, given a valid original | Proved (`erased_digit_unique`); uppercase spellings of one digit are aliases |
| `decode_readings` returns all and only the distinct valid data | Tests; enumeration specification and proof remain |
| Known answers match the specification | Ten kernel-checked cases; another 1,100 shared vectors run through compiled Lean |
| Optimized Rust implements the specification, including failures | Tests; refinement proof remains |
| Bob's actual executable implements the specification | Executable-byte proof remains |
| Every result Bob uses is checked for its specific input before use | Kernel-checking machinery exists for reference-proposed answers; accepting arbitrary executable results and the checked-use workflow remain to implement |
| Execution has no memory errors, invalid shifts or unintended overflow | Safe Rust provides substantial protection; comprehensive implementation proof remains |
| Operations terminate within affordable work and allocation bounds | Lean definitions terminate; finite-machine resource contracts and proofs remain |
| Concurrent calls behave correctly | Shared initialization and memoization need coverage in the implementation proof |
| Output and exit status faithfully report the result | Requires coverage of the surrounding application |
| Execution reveals no secrets through timing or other unintended channels | Requires an explicit leakage model, including allocation and surrounding code |
| Advertised look-alike attack costs hold | Precise adversary and digit-distribution analysis remains |

The format uses N = 1,353 alphabet digits and encodes the input's numeric
value multiplied by K. `Sigil.Prime` states mathematical primality explicitly:
at least two, with only one and itself as natural-number divisors.
`isPrime_iff` connects this to trial division; `layout_contract` states the
layout guarantees together.

The universal error-control proofs cover every digit value, position and
byte length. Mathematical uniqueness of an erased digit and correctness of
the enumeration program are separate obligations.

Round-trip correctness also leaves a separate obligation: the encoder and
decoder must agree with Bob's intended format. Two implementations of the
same mistaken format can round-trip perfectly.

The look-alike figures of 10.4 bits per compared character and 83 bits for
eight characters are approximate capacity estimates, with no proved attack
work factor. Valid sigils have dependent digits and a restricted first
digit. Jumbling structured input also needs a security argument for that
input's validity constraints.

## Dynamic assurance: check each result before using it

Bob can check each encoding or decoding operation at the time he needs it,
using his specific input and the specific result he is about to use. He
repeats the check for every operation whose answer he wants certified.

The proposed workflow is:

1. Bob records the exact input and, for decoding, its expected byte length.
2. Any implementation produces a candidate answer, including a claimed
   decoding error where appropriate.
3. A local tool places that input and candidate answer in a fixed-form
   theorem with explicit byte/code-point literals.
4. Lean's kernel checks that the specification gives that exact answer.
5. Bob uses the certified answer only after the check succeeds. A failed,
   interrupted or resource-exhausted check leaves the answer unverified.

This is **dynamic, per-operation assurance**. The theorem establishes
`encode(this input) = this answer`, or the corresponding decoding result
or exact error. An entirely new input receives the same check; past success
on a finite test corpus is separate evidence. If a planted rare trigger
produces a wrong answer, its theorem fails on that triggering input too.

For the correctness of that accepted answer, Bob can remove reliance on
the producer and its compiler. He retains reliance on the reviewed
specification, proof checker and its foundations, input/output
correspondence, and the environment running the check. The checker itself
has a compiler/build chain that also deserves scrutiny.

This assurance covers a result. A universal executable proof instead covers
all permitted executions of particular bytes. Side effects, leakage and a
producer that hangs need separate protection; a producer running with
access to the checker could also interfere with the check. Isolation can
separate those responsibilities. Bob also needs the answer he uses to be
the one whose literals the theorem certified.

The current `tools/certificate.py` proposes answers using the Python
reference and emits statements for kernel checking. Bob can also write a
literal statement for another producer's candidate answer himself. A tool
that directly accepts that producer's claimed answer, checks it with bounded
resources and enforces checked use is deferred until it demonstrates a
materially smaller reliance set and a practical integration path. Kernel
recomputation can be expensive; an efficient proof-producing implementation
could reduce the checking work while preserving the same assurance boundary.

## Verification paths and their reliances

**●** means relied upon. **—** means that path can avoid relying on the
component's correctness, under the qualifications below. These are possible
paths; Sigil currently provides reference-proposed kernel-checked answers
and the specification proofs. The arbitrary-candidate workflow above and
Rust/executable proofs remain open.

| Verification path | Answer-producing implementation | Rust compiler/linker | Source-to-proof extractor | Lean native compiler/runtime | Proof checker | Machine-code semantics |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Run Rust and compare test vectors | ● | ● | — | — | — | — |
| Prove extracted Rust, then compile normally | —¹ | ● | ● | — | ● | — |
| Prove a Lean implementation, then compile normally | —¹ | —² | — | ● | ● | — |
| Dynamically kernel-check each specific input/result before use | — | — | — | —³ | ● | — |
| Check a correctness certificate for Bob's executable bytes | — | — | —⁴ | —⁴ | ● | ● |

1. The implementation can be adversarial: a sound proof covering its full
   behaviour should reject a violating special case. Proof scope includes
   every precondition on which the theorem depends.
2. Other native toolchains may replace Rust's compiler in the reliance set.
3. Kernel reduction supplies the computation. Bob still relies on the
   executable containing the kernel itself, including how it was built.
4. This requires a checked connection from the actual bytes to the
   specification that avoids trusting those intermediate steps. A source
   proof alone leaves compilation and linking outside its claim.

Every path also relies on the intended specification, correct input/output
correspondence, and the relevant hardware and operating-system behaviour.
A machine-code model brings its own assumptions: a proof against an
inaccurate model establishes the model's behaviour alone.

A Lean theorem about a function and native execution of that function have
different reliance sets. The kernel checks the theorem; the compiler and
runtime produce and execute the native code.

## Reliances Bob might want to reduce

| Reliance | How Bob might reduce it |
|---|---|
| Our claims and documentation | Read the theorem statements and definitions |
| Our alphabet generator and Unicode-property interpretation | Independently reproduce the alphabet and review or prove its rules |
| Our test-vector or answer generator | Use independently calculated examples and kernel-check proposed answers |
| Our prover or solver | Accept independently checkable proof certificates |
| A source-to-Lean translator | Validate the translation independently, or verify the resulting machine code directly |
| Rust, LLVM and linker correctness | Dynamically check each answer before use, or check a universal correctness certificate for the executable bytes they produced |
| Lean's native compiler | Use kernel-checked answers for particular inputs |
| A particular proof-checker implementation | Check through independent kernels |
| The compiler that built the proof checker | Investigate with diverse double compilation and independent implementations |
| Cached proof artifacts | Recheck with `--trust=0`; also establish correspondence to reviewed source |
| Our build server and release artifacts | Build locally and check the resulting bytes |
| A renderer, terminal or clipboard | Inspect explicit byte/code-point literals and verify what reaches the consuming application |
| Libraries, startup code, allocator and dynamic loader | Include them in the verified boundary, or make their contracts explicit and minimize that boundary |

Reproducible builds establish agreement. A compiler backdoor can produce
reproducible output too. Diverse double compilation is a separate technique
for investigating a compiler's correspondence to its source, under its own
independence and environment assumptions.

For kernel-checked answers, the generator can propose any answer it likes;
the checker verifies its theorem. Bob must still inspect which question the
theorem asks. A malicious generator can state a correct answer to a different
input, and a malicious UI can display an unrelated result beside a valid
proof. The statement's explicit literals are the certified input and output.

The existing proofs use only subsets of Lean's standard axioms (`propext`,
`Classical.choice`, `Quot.sound`), with no `sorry` or `native_decide`.
Run `lake env lean --trust=0 Audit.lean` from `lean/` after `lake build` to
inspect the main statements and axiom lists. Checking imported declarations
establishes their logical validity; Bob also reviews whether those
declarations describe his intended format.

## The devastating rare-trigger case

Bob's strongest useful demand is:

> For every input satisfying this contract, these exact executable bytes
> produce the specified result or specified failure, within these resource
> bounds.

A universal proof rules out a planted special case inside the covered
behaviour. A finite known-answer corpus supplies valuable evidence while
leaving untested inputs open.

The executable claim must cover reachable helpers and any runtime or
external calls, with their assumptions stated. A command-line tool also
needs its input parsing, output and exit status covered. A proof of an
isolated encoding function leaves those surrounding behaviours open.

"No backdoors" becomes a precise obligation through that behavioural
statement plus explicit information-flow and side-channel requirements.
A program can return every correct answer while leaking its input.

## Our destination and present foothold

The priority is a universal certificate about **Bob's own build's executable
bytes**, checked against a short specification and statement he inspects,
through a checker he chooses. That connection is still open. Dynamic
per-answer checking is an alternative path; a complete static proof would
make it redundant for the same functional claims. Further dynamic-tool
integration is deferred until its reliance set and workflow earn their cost.

Today Bob can kernel-check particular encoding and decoding answers and
the specification's universal mathematical guarantees. The Lean definitions
also have a value for an empty byte list; the public implementations require
at least one byte.

An Aeneas scratch experiment has translated a carry-propagating Rust
multiply-add loop into Lean and built it against the Aeneas library. That
establishes feasibility for a small example. Sigil's Rust refinement proof
remains open. Source-level proofs can help develop the arithmetic invariants
while an executable-level proof or independently checked translation closes
the remaining compilation boundary.

A [static AArch64 probe](experiments/static-arm64/README.md) now proves a
multiply-add primitive's exact modeled state change, including return and
preservation of all state except X0 and PC. It binds the final linked
library's instruction bytes to the proof and calls the routine through a
C ABI. Sigil's complete encoding/decoding proof remains open. The historical
model toolchain, missing division instructions and loader/caller boundaries
remain explicit adoption gates. The experiment motivates investigating a
small assembly core while keeping the current implementations as oracles.
