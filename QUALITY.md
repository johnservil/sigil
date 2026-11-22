# Quality

How Sigil is checked, what that shows, and what it does not show yet. Each
line names the check, so you can run it yourself (README.md, "Reproduce and
test").

## Checked on every push

The [CI workflow](.github/workflows/ci.yml) runs these on every push and
pull request:

| what | check | shows |
|---|---|---|
| The alphabet | `alphabet/alphabet.py --check` | `alphabet.txt` and `skipped.txt` follow [REQUIREMENTS.md](REQUIREMENTS.md)'s "The alphabet" from the data of every Unicode release from 6.0.0 to 18.0.0 (each file checked by SHA-256 and BLAKE3) and the font tests in `alphabet/font-tests` |
| The shared vectors | `python/vectors.py --check` | `vectors.json` and `vectors.tsv` are the reference implementation's output: 185 encodings, 518 variants (skipped characters inserted, the mark gone, the handle in uppercase), and 851 errors of every kind |
| The reference (Python) | `python/test.py` | it passes the vectors; every one of 903,080 changed characters (a hex digit for a hex digit, a letter for a letter) and 1,128 swaps of characters one or two apart, in 20 random 256-bit sigils, fails to decode; one unread letter or hex digit comes back; the first letter after the handle takes 2,047 of the 2,048 values and the last all of them; the layout is right at every length to 1,024 bytes |
| Rust | `cargo test` in `rust/` | it passes the vectors; K's table follows the rule in README.md and no larger prime passes it; every letter reads back as its digit; data of every length to 300 bytes round-trips; 20,000 random sigils round-trip, and their corrupted copies never make decoding panic and decode only to data that re-encodes to their letters |
| TypeScript and the browser | `typescript/dist/test.js`, `tools/build-web.py --check`, `tools/test-web.py` | TypeScript passes the vectors; the browser bundles are the compiled TypeScript; 1,781 checks of the bundles, the extension and the playground pass in Chrome |
| The Lean specification | `lake build`, `lake exe tests` and `lean --trust=0 Audit.lean` in `lean/`; `tools/test_certificate.py` | the specification passes the vectors; the proofs below check, on Lean's standard axioms alone; Lean's kernel accepts particular answers of the specification and refuses deliberately wrong ones |

## Proved, in Lean

Lean's kernel checks every step, and every proof rests on Lean's three
standard axioms alone (`lean/Audit.lean`, run with `--trust=0`).

- For every length, K is a prime larger than 2,048 that fits beside the
  marked bits, in the fewest letters (`layout_contract`).
- The facts a round-trip proof is built from (`lean/Sigil/Facts.lean`): the
  letters are distinct, never skipped and never hex digits; each letter and
  each hex digit reads back as its value; the marker goes in and comes out;
  bytes and digits convert back and forth.

**Not carried to 0.2 yet.** For 0.1's format Lean also proved that decoding
any data's sigil gives the data back, that a changed letter and a swap of
letters one or two apart always fail the check, that one erased letter has
only one valid value, and eleven known answers. Those proofs are at the tag
`v0.1.2+5404f5e7b0912b58eb7d34006c7fb5c73cd4ecc7`. In 0.2's format a handle
of hex digits takes part in the check, and 0.2 is a release on trial: its
proofs wait until the format settles. Until then these properties are
tested (the table above), not proved.

## Checked by hand at the release

- **Reproducible:** `cargo package` at the tag gives the crate crates.io
  serves, byte for byte; its SHA-256 and BLAKE3 are in the GitHub release.
- **Timing:** the Rust takes time linear in the data's length, and took the
  same time for all zeros, all ones and random data within 2%, in one run in
  a virtual machine (`rust/examples/bench.rs`).

## Not shown yet

- **Constant time** rests on the Rust's design (no branch, table index or
  division on the data's value) and that one measurement. A statistical
  test over many runs, with cycle counts, and a look at the compiled code
  remain to do.
- **The Rust implements the specification:** tested, not proved.
- **K's selection rule** is checked by the reference and the Rust test, not
  proved in Lean; Lean proves what correctness needs of each K.
- **No fuzzing** beyond the randomized test above, and no mutation testing
  of the test suites.
- **No independent review** yet.
- **Comparing by eye:** how reliably people tell the letters apart has not
  been measured, so Sigil claims nothing about it.
- **Fonts:** twenty tests on five systems; more devices, Windows and
  Android above all, make the evidence stronger
  ([the font test](https://johnservil.github.io/sigil-candidates/check.html)).
