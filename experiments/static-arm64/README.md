# Static machine-code proof: feasibility probe

This experiment establishes a small but real connection from a linked
AArch64 library's instruction bytes to a universal arithmetic theorem.
It also exercises the same function through a C ABI and a linked C
executable. It leaves Sigil's production implementations unchanged.

**Scope:** one multiply-add primitive. This is neither a verified Sigil
encoder/decoder nor a proof of the loader or surrounding application.
The historical model toolchain is isolated here as investigation evidence,
not adopted as a supported Sigil verification dependency.

## Reproduce

On native AArch64 Linux, with GCC/binutils, git, CPython and elan/lake on
PATH, from the repository root:

```sh
python3 experiments/static-arm64/check.py /tmp/sigil-static-new
```

The directory must be new. Downloads, generated statements and builds stay
there. Elan installs the model's pinned toolchain if needed. The main
`lean/` project and its toolchain are unchanged. No benchmark is run.

The check:

1. Fetches LNSym at the exact commit below. It replaces only Lake packaging
   to exclude unused ELF/documentation dependencies, leaving model source
   and upstream proofs unchanged.
2. Checks `Probe.lean`, then rechecks with `--trust=0`. The final theorems
   depend only on `propext`, `Classical.choice` and `Quot.sound`.
3. Assembles `muladd.S` and links `libsigil_static_probe.so` without a C
   runtime. It extracts `.text` from the **final shared library** and asks
   Lean to prove equality with `codeBytes`.
4. Flips one extracted byte and requires Lean to reject the same equality.
5. Calls the library on 125 edge cases and 1,000 deterministic random
   triples against Python integer arithmetic, then builds and runs
   `caller.c` through the exported C ABI in `muladd.h`.

All five steps pass in the native AArch64 Linux VM. The native calls and C
executable are integration/model-agreement evidence; the universal
arithmetic result comes from the proof.

## The statement and its bytes

The routine is:

```asm
madd x0, x0, x1, x2
ret
```

Its little-endian bytes are `00 08 01 9b c0 03 5f d6`. The proof builds the
instruction map from those bytes and proves that LNSym decodes them as MADD
and RET. Quantification covers every modeled initial state and load address
whose PC and instruction map satisfy the stated preconditions and whose
initial error state is clear.

`muladd_word_state` gives the **exact final state after two steps**:

- X0 becomes X2 + X0·X1, modulo 2^64.
- PC becomes the original link-register value, X30.
- Every other modeled register, flags, memory and program map is preserved,
  including the error state.

`muladd_word_exact` adds three preconditions: X0, X1 and X2 are each below
2^32. It proves the returned natural number is exactly word·multiplier +
carry, with no wraparound. This is the arithmetic used by Sigil's 32-bit
limb multiply-add, but its memory loop and connection to the encoding are
still to prove.

These are static theorems for all such inputs. Calling the library needs
no Lean installation and performs no per-operation proof check.

## Reliances and boundaries

For this primitive's modeled behaviour, the proof plus byte equality removes
the assembler and linker from the correctness reliance set: a changed
instruction stream fails the equality check. The theorem's scope remains
the routine entered under its preconditions, not arbitrary behaviour of an
ELF file containing it.

Bob still relies on:

- Lean's kernel binary, its foundations and the stated axioms, including
  the checker binary's build chain.
- LNSym's decoder and instruction/state semantics matching the relevant
  hardware behaviour. This is a third-party Lean model, not a proof against
  Arm's own ASL. Native tests supply evidence, not that connection's proof.
- The correspondence between the actual loaded instructions and the
  extracted byte literals. The script uses `objcopy` and a short Python
  conversion; Bob can extract and compare them with his own tools.
- A valid execution environment: instruction mapping, permissions,
  alignment, return address and the ABI. The flat model separates program
  instructions from data memory and does not model the whole MMU/OS.

ELF metadata, initialization, symbol resolution and loading, the C caller,
startup code, output and exit status remain outside the proof. The shared
library is a convenient integration experiment, not a claim that arbitrary
compiler/linker sabotage elsewhere in the ELF is excluded. The proof also
makes no microarchitectural timing or leakage claim.

A deployable verified library must bind its exported entry points and all
reachable code/data to its certificate, with loader assumptions explicit.
A verified command-line executable additionally needs parsing, output,
system calls and exit status covered. Proving the isolated routine is an
initial building block for those larger claims.

## Models investigated

| Candidate | Revision examined | Finding |
|---|---|---|
| [LNSym](https://github.com/leanprover/LNSym) | `5c05220ff970e3bdd7813ad0c9ef3741522c8b92` | This probe builds and proves exact instruction-state behaviour. Uses `leanprover/lean4:nightly-2024-10-07`; native long multiply and divide instructions needed by straightforward Sigil arithmetic are incomplete. |
| [Lean bignum](https://github.com/cslib-community/bignum) | `4b799508320060897290f47d371c825e002f0f24` | Current port of s2n-bignum's framework. At this revision the decoder handles add/sub immediate, with flag-setting cases unimplemented; its simple tutorial theorem is unfinished. Needs more instruction coverage for Sigil. |

The LNSym MADD form used here is implemented. UMADDL/UMULH are marked
unimplemented; its two-source execution function handles variable shifts
and omits UDIV. A direct build on Sigil's Lean 4.31.0 fails on changed
BitVec APIs and removed theorem names. The historical toolchain therefore
establishes feasibility, while model/toolchain maintenance remains a gate
before adoption.

The fork's ongoing Arm-ASL parser/interpreter work offers another way to
reduce reliance on a manually transcribed model. Its interpreter and
instruction proofs are unfinished, so it is not yet a drop-in alternative.

## Decision and next steps

The experiment supports pursuing a **small assembly core with a C ABI**:
we can check real bytes once, prove a complete state change including return,
and call the resulting function from an ordinary executable. Assembly can
keep allocator and language-runtime machinery outside the core.

It does not yet establish which model is the lowest-cost maintained route
for the complete implementation. Before replacing Sigil:

1. Choose the model/toolchain maintenance path and confirm coverage of the
   full proposed instruction subset, particularly division and memory.
2. Write the full callable encoder/decoder contract, including caller-owned
   buffers, malformed inputs, allowed writes, work bounds and ABI state.
3. Prove the arithmetic and memory loops, then the alphabet/text operations,
   against Sigil's existing format definitions for all supported lengths.
4. Bind the proof to the final linked entries and reachable instructions;
   state or verify the loader and application boundary.
5. Compare native results with the current implementations and measure
   through `clocks` before considering production replacement.

The current implementations remain test oracles during the investigation.
Dynamic answer-checking integration is deferred: the static route is the
priority, and a universal executable proof would cover the same functional
claims without per-call checking.
