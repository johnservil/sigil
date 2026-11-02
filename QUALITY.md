# Quality

How Sigil is checked, what that shows, and what it does not show yet. Each
line names the check, so you can run it yourself (README.md, "Reproduce and
test").

## Checked on every push

The [CI workflow](.github/workflows/ci.yml) runs these on every push and
pull request:

| what | check | shows |
|---|---|---|
| The alphabet | `alphabet/alphabet.py --check` | `alphabet.txt` and `skipped.txt` follow [alphabet/RULES.md](alphabet/RULES.md) from Unicode 14.0.0's data (each file checked by SHA-256 and BLAKE3) and the font tests in `alphabet/fonts.txt` |
| The shared vectors | `python/vectors.py --check` | `vectors.json` and `vectors.tsv` are the reference implementation's output: 220 encodings, 484 variants with skipped characters inserted, and 748 errors of every kind |
| The reference (Python) | `python/test.py` | it passes the vectors; every one of 1,023,500 changed letters and 939 swaps of letters one or two apart, in 20 random 256-bit sigils, fails the check; one unread letter comes back; the first and last letters each take all 2,048 values; the layout is right at every length to 1,024 bytes |
| Rust | `cargo test` in `rust/` | it passes the vectors; K's table follows the rule in README.md and no larger prime passes it; every letter reads back as its digit; data of every length to 300 bytes round-trips; 20,000 random sigils round-trip, and their corrupted copies never make decoding panic and decode only to data that re-encodes to their letters |
| TypeScript and the browser | `typescript/dist/test.js`, `tools/build-web.py --check`, `tools/test-web.py` | TypeScript passes the vectors; the browser bundles are the compiled TypeScript; 1,712 checks of the bundles, the extension and the playground pass in Chrome |
| The Lean specification | `lake build` and `lake exe tests` in `lean/` | the proofs below check, and the specification passes the vectors |

## Proved, in Lean

Lean's kernel checks every step, and every proof rests on Lean's three
standard axioms alone (`lean/Audit.lean`, run with `--trust=0`). For every
length and every position:

- decoding any data's sigil gives the data back (`decode_encode`);
- K is a prime larger than 2,048 that fits beside the marked data, in the
  fewest letters (`layout_contract`);
- a changed letter, a swap of neighbours, and a swap of letters two apart
  always fail the check (`single_change_detected`, `adjacent_swap_detected`,
  `two_apart_swap_detected`), and one erased letter has only one valid value
  (`erased_digit_unique`).

Eleven known answers are checked by the kernel too, and
`tools/test_certificate.py` shows that Lean refuses deliberately wrong
answers. Both take about ten minutes and more memory than CI's runners
have, so they run by hand: they passed at the 0.1 release.

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
- **Fonts:** twelve tests on five systems; more devices, Windows and
  Android above all, make the evidence stronger
  ([the font test](https://johnservil.github.io/sigil-candidates/check.html)).
