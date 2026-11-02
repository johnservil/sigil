# Changes

## Sigil 0.1.1+a04b2b9b525bd58126b62bb66938f58b2adeb53f, November 2026: a README on crates.io

The crate's page on crates.io shows a README. The code is 0.1's.

## Sigil 0.1, November 2026: the first release

Sigil's first release changes how sigils look, so a sigil made before it
won't decode now. The earlier format was never released as a package; the
first release on crates.io, `sigilcode` 0.1, has the new one.

What changed:

- **A new alphabet of 2,048 letters** from fifteen scripts, chosen by
  rules anyone can check ([alphabet/RULES.md](alphabet/RULES.md)) and drawn
  by every device tested on macOS, iOS, Windows, Android and Linux.
- **Shorter sigils:** a 256-bit hash takes 25 letters, where it took 26.
- **No hex digits,** and no letters that look like them, so a sigil and hex
  are told apart at a glance.
- **No upper and lower case,** so software that changes case leaves a sigil
  as it was.
- **Every letter is three bytes of UTF-8,** so every sigil of a size has the
  same length however you count.
- **Linear time and memory:** encoding and decoding take time and memory in
  proportion to the data's length, where they grew with its square before.
- **The same time for any data:** the Rust crate is built to take the same
  time to encode or decode, whatever the data's value, so timing reveals
  nothing about it.
- **Stricter reading:** decoding skips spaces, line breaks and the invisible
  characters copying inserts, and refuses everything else, so what you see
  is what decodes.
- **Room for what comes next:** every sigil carries two marker bits, `01`,
  between its data's halves. A later format puts another value there, so its
  strings and Sigil's never decode as each other, and a string of another
  format fails with its own error, `marker`.
- **One answer from uncertain readings:** `decode_readings` returns the data
  that the one valid reading encodes, or fails with `ambiguous` when several
  readings decode, where it returned a list.

The hash of nothing, `BLAKE3("")`, is now `ᢳᕌᔃጾዿᑂഔጕꔍⶰᣟꕄꕛቴⴲజᐽᙿᕯⶂጁᑃሃᛜጩ`.
