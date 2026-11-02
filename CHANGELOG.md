# Changes

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
  same length however you count, and encoding in Rust takes the same time
  whatever the data.
- **Stricter reading:** decoding skips spaces, line breaks and the invisible
  characters copying inserts, and refuses everything else, so what you see
  is what decodes.

The hash of nothing, `BLAKE3("")`, is now `ᢳᕌᔃጾዿᑂഔጕꔍⶰᣟꕄꕛቴⴲజᐽᙿᕯⶂጁᑃሃᛜጩ`.
