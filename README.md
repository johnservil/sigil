# Sigil

Sigil writes bytes as a sigil: one word of letters and digits that a person
can copy with a double-click, compare at a glance, and read back from a
picture. A 256-bit hash becomes 26 characters, no two of which look alike.

```
BLAKE3("") in hex    af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            in base64 rxNJufX5oaagQE3qNtzJSZvLJcmtwRK3zJqTyuQfMmI
            as a sigil ᑖɬđዴᔕħɂᗔʐᓪcᣕጔэⶈᓄᕖχɐᖃⷁሾቹᒱaጹ
```

Its 1,353 characters are digits and letters of five scripts: Latin, Greek,
Cyrillic, Ethiopic and Canadian syllabics. Every one runs left to right, and
Unicode treats a run of them as one word that never breaks across lines. A
sigil looks like nothing else in a text, and it looks wonderful.

## When to use it

Sigil serves values that people copy, compare and photograph: hashes, keys
and identifiers in a status line, a chat, an email, a web page or a printout.

| a 256-bit value | characters | bits a forger matches per compared character | a double-click selects | a misread character |
|---|---|---|---|---|
| hex | 64 | 4 | the whole value | goes unnoticed |
| base32 | 52 | 5 | the whole value | goes unnoticed |
| base64 | 43 | under 6 (`I` `l` `1` and `O` `0` look alike) | part of it, wherever `+`, `/` or `-` falls | goes unnoticed |
| **sigil** | **26** | **10.4** | **the whole value** | **is caught, and repaired from a few readings** |

Its properties work together:

- **Short.** A sigil takes 26 characters where hex takes 64, so two of
  them, labelled, fit GitHub's 140-character status description.
- **Copied with one gesture.** A double-click selects the whole sigil, and
  copying it carries nothing else. Decoding skips any white space or
  invisible characters that a line break or a copy inserts, and reads
  letters in either case.
- **Hard to imitate.** No two characters look alike, so for a hash or a key
  each character a person compares costs a forger 10.4 bits ("Telling
  sigils apart"): 83 bits for the first and last four, where hex's first
  and last four cost 32.
- **Read back by machines.** Fonts on the major platforms draw every
  character, no character or sequence of characters looks like another, and
  a check confirms a reading or picks the right one of several ("Reading
  sigils by machine").
- **Recognized at a glance.** A word of glyphs from five scripts at once is
  unlike any word of any language, so a reader who meets one knows what it
  is: a sigil, which Sigil decodes. A string of hex could be a number, a
  colour or a hash from any of a dozen functions, and base64 could be any
  token at all.
- **Beautiful.** A sigil looks like a seal cut in an old alphabet: something
  worth showing, and worth asking about.

Other encodings serve other channels:

- **Typed by hand or read aloud:** hex, or z-base-32, whose letters are
  chosen for people to type.
- **Bytes at a premium** (URLs, database columns): base64, at 43 bytes. A
  sigil's characters take 1 to 3 bytes in UTF-8, about 72 for 256 bits.
- **ASCII only:** hex or base64.

## Use it

Decoding takes the length in bytes that the sigil encodes. The encoder and
decoder agree on it in advance: a 256-bit hash is always 32 bytes.

Python (`python/sigilcode.py`):

```python
import sigilcode
sigil = sigilcode.encode(digest)            # 26 characters for 32 bytes
digest = sigilcode.decode(sigil, 32)        # raises sigilcode.DecodeError
found = sigilcode.decode_readings(readings, 32)   # readings: each character's possible readings
```

TypeScript (`typescript/sigilcode.ts`, in browsers and Node):

```typescript
import { encode, decode, decodeReadings, DecodeError } from "sigilcode";
const sigil = encode(digest);               // digest: a Uint8Array
const back = decode(sigil, 32);             // throws DecodeError
```

Rust (`rust/`, crate `sigilcode`, no dependencies):

```rust
let sigil = sigilcode::encode(&digest);
let back = sigilcode::decode(&sigil, 32)?;  // Err(DecodeError)
```

**Structured data: jumble it first.** Sigil writes the data in order, and
its protection against look-alikes holds for data that looks random: a
secure hash's output, a key, a random identifier. If your data has
structure (fields, several keys or hashes together, a counter or a
timestamp), jumble it before you encode it and unjumble it after you decode
it, with F4Jumble (Zcash's ZIP 316) or a few Feistel rounds of a secure
hash such as BLAKE3. The jumble must be built from a secure hash: a forger
solves a simpler mix (a linear one, say) for the bytes they control.
"Telling sigils apart" says why.

A decode error has one of four kinds: `length` (the wrong number of
characters), `character` (one outside the alphabet), `range` (a value too
large for the length) and `check` (the check fails). The last two mean a
character was misread or changed.

## Telling sigils apart

People compare sigils by eye, often only their first and last few
characters. Someone who wants a sigil that looks like yours must produce
data whose sigil looks like it: for a hash, they can only try inputs until
one hashes to a look-alike, and for a key, generate keys. Each character a
person compares makes them match that character exactly, since no two
characters of the alphabet look alike: a chance of 1 in 1,353, or 10.4
bits, for every compared character. Fewer characters, each carrying more
information, make every sigil harder to imitate.

This holds for the output of a secure hash, and for keys and identifiers
drawn at random: every bit of such data depends on the whole input, so a
forger who changes anything changes every character. Sigil writes the data's
bytes in order, the first bytes in the first characters, and mixes nothing
of its own into them, since mixing would give such data nothing more.

Data with structure shows it. Counters and timestamps give sigils that share
their first characters. A forger who can copy parts of some data (one of the
keys in an address, one of a pair of hashes) can keep its ends and change
its middle. So if your data has structure, you must jumble it before
encoding it, as Zcash's F4Jumble does for its unified addresses: then every
character depends on every bit, and a forger who keeps your parts must try
their own until the ends match, at 10.4 bits for each compared character.

<details>
<summary>Why Sigil writes the data in order</summary>

An encoding can jumble the data before writing it: a few rounds of a hash
over its two halves, as F4Jumble does, so that every character depends on
every bit. What jumbling would do depends on what a forger controls:

- **A secure hash's output, a key, a random identifier: nothing.** The
  forger can only try inputs, or generate keys, and every result is random
  in every position, jumbled or not. Matching the first and last four
  characters costs 83 bits either way.
- **Data the forger chooses entirely: nothing.** Jumbling is public and
  invertible: the forger writes a jumbled value with the victim's ends and
  runs the rounds backwards.
- **Data built of parts a forger can copy: protection.** Without jumbling,
  the forger keeps the victim's parts at the ends and puts their own in the
  middle, and the ends match for free. With it, any change changes every
  character, and since the data must still hold the copied parts, the forger
  must try their own part until the ends match: 10.4 bits for each compared
  character.

Most of Sigil's data is the first kind. Jumbling inside Sigil would cost
every call five BLAKE3 compressions where one serves (38% of encoding's
time in the Rust), and every implementation its rounds, their inverse and
their tests, for data that gains nothing. So Sigil leaves jumbling to the
callers whose data is the third kind: they jumble it before encoding.
</details>

## Reading sigils by machine

A sigil photographed or printed can be read back by optical character
recognition (OCR). Three properties serve it:

- **Every character is drawn.** The alphabet keeps scripts whose fonts the
  major platforms ship, so a picture of a sigil shows its characters, never
  boxes.
- **Nothing looks alike.** No two characters look alike, and no character
  looks like a sequence of others (as `m` looks like `rn`), by Unicode's
  table of look-alikes (UTS #39). A reader that recognizes the shapes can
  tell every character apart.
- **The check confirms a reading.** A sigil carries a check, 14 bits for a
  256-bit value, so a wrong reading almost always fails to decode. A reader
  unsure of a character passes its few likeliest readings to
  `decode_readings`, which returns the data that the one valid reading
  encodes. With three readings for one character, the right data comes back
  alone practically always (200 of 200 in the tests); with one character
  unread altogether, every character tried in its place, about 92 times in
  100.

## The encoding

Sigil encodes data of L bytes, L ≥ 1:

1. **Layout.** Let m be the fewest characters that hold 8L bits, the
   smallest m with N^m ≥ 2^(8L), where N = 1,353. The sigil has n = m + 1
   characters, and its check has c bits, all the room left: the most c with
   2^(8L + c) ≤ N^n.
2. **Check.** t is the first c bits of BLAKE3 in derive-key mode, with
   context string `Sigil 2026-10-22 check`, over the data.
3. **Write.** The value w = d · 2^c + t, where d is the data as a number,
   most significant byte first, written in base N with exactly n digits,
   most significant first. Digit d is the d-th character of the
   alphabet (`alphabet.txt`, in ascending code point order).

| L (bytes) | 16 | 20 | 32 | 48 | 64 |
|---|---|---|---|---|---|
| n (characters) | 14 | 17 | 26 | 38 | 51 |
| c (check bits) | 17 | 16 | 14 | 11 | 18 |

A decoder told L first drops every character that Unicode 14.0 marks
White_Space or Default_Ignorable_Code_Point (the ranges in `ignored.txt`).
It reads each remaining character as its digit, a letter's uppercase
(`uppercase.txt`, in the alphabet's order) as the letter. It requires
exactly n characters, each in the alphabet or its uppercase, and a value w
below 2^(8L + c) whose low c bits are the check of the rest, the data.

The layout gives every length a check of at least one character's worth,
and the alphabet's size is chosen for 256-bit data: 25 characters hold it,
and the 26th gives the check its 14 bits.

## The alphabet

`alphabet/alphabet.py` computes the alphabet from Unicode 14.0.0's data
files, by itself: it downloads each file (or reads a saved copy), checks its
SHA-256 and its BLAKE3 before using it, and reads every property from the
files. So the same files give the same alphabet with any Python 3 on any
machine. Each rule keeps the characters that pass it:

| rule | removes | left |
|---|---:|---:|
| in the Basic Multilingual Plane | 1,048,576 | 65,536 |
| assigned (not a surrogate) | 48,652 | 16,884 |
| assigned by Unicode 5.2 (2009) or earlier | 1,208 | 15,676 |
| a lowercase letter (Ll), a caseless letter (Lo), or an ASCII digit | 7,337 | 8,339 |
| left-to-right: a letter of bidi class L, or a digit of class EN | 1,130 | 7,209 |
| unchanged by NFC, NFD, NFKC and NFKD | 1,245 | 5,964 |
| its uppercase is one character, which lowercases and case-folds back to it | 3 | 5,961 |
| neither default-ignorable nor white space | 2 | 5,959 |
| never the second half of a composition | 48 | 5,911 |
| non-joining (joining type U) | 173 | 5,738 |
| joins its neighbours into one word (word break ALetter, or Numeric for a digit) | 609 | 5,129 |
| never a line break beside its neighbours (line break AL, or NU for a digit) | 1,537 | 3,592 |
| Latin, Greek or Cyrillic below U+0800, Ethiopic or Canadian syllabics, or an ASCII digit | 2,113 | 1,479 |
| the lowest code point of its class of look-alikes (UTS #39) | 104 | 1,375 |
| looks like no sequence of the others (UTS #39) | 22 | **1,353** |

<details>
<summary>What each rule protects</summary>

- **The Basic Multilingual Plane.** GitHub refuses 4-byte UTF-8 in a status
  description, and characters beyond the plane need UTF-16 surrogate pairs,
  which software splits.
- **Unicode 5.2 or earlier.** Fonts lag new letters: DejaVu, a common Linux
  default, lacks the Cyrillic letters that Unicode 6.0 and 7.0 added.
- **Letters and digits.** They survive where symbols and punctuation are
  rewritten or dropped.
- **Left-to-right.** Every character displays in the order it is stored, in
  any paragraph.
- **Unchanged by normalization.** Software normalizes text (older Mac file
  systems to NFD, web forms to NFC); every character stays itself.
- **An uppercase that maps back.** Software that changes case leaves a sigil
  decodable: decoding reads each letter's uppercase as the letter.
- **No interaction between characters.** The next three rules exclude
  invisible characters, two characters normalizing into one, and cursive
  joining. Each excludes both sides of an interaction.
- **One word.** Unicode's word rules (UAX #29) join these letters and digits
  into one word, which a double-click selects whole.
- **One line.** Unicode's line rules (UAX #14) allow no break between them,
  so a sigil stays on one line.
- **Scripts with fonts.** A missing glyph shows as a box, and boxes hide
  which character is which. macOS draws every Ethiopic and Canadian
  syllabic the alphabet keeps; DejaVu lacks parts of the Latin and Cyrillic
  extension blocks above U+0800, which the alphabet leaves out.
- **One character per class of look-alikes.** Of characters that Unicode's
  table of look-alikes (UTS #39) gives one skeleton, the lowest code point
  stays. Every compared character then tells its class apart from every
  other, for a person and for OCR.
- **No sequence look-alikes.** Unicode's table says `m` looks like `rn`, and
  a syllabic with a dot like the dot final and the syllabic. While a
  character's skeleton is the skeletons of others in a row, the character
  that ends the most such spellings goes: the look-alike itself, or a piece
  of its spelling outside ASCII (ties to the lowest code point). Every
  ASCII digit and letter that the earlier rules keep stays but `m`.
</details>

## Evidence

- **The encoding:** all three implementations pass `vectors.json` (or its
  twin, `vectors.tsv`): 220 encodings, 528 variants (copies with white space
  or invisible characters inserted, or letters in uppercase) and 352 errors,
  each of the kind it must give. Each implementation's BLAKE3 agrees with
  BLAKE3's official test vectors, hashing and deriving keys (the Python
  tests check all 35).
- **Readings:** with three readings for one character of a 256-bit sigil,
  `decode_readings` returned the right data alone in 200 of 200 tests; with
  one character unread, in 37 of 40.
- **A specification in Lean** (`lean/`): "The encoding" as Lean
  definitions, over C2SP's BLAKE3 specification and the alphabet that
  `alphabet/alphabet.py` writes; it passes `vectors.tsv` too.
- **Speed** (`rust/examples/bench.rs`): the Rust encodes a 256-bit value in
  0.58 µs and decodes it in 0.69 µs, in a Linux virtual machine on an Apple
  M4 Max.
- **Selection** (`copytest.html`): a double-click selects whole sigils in
  Chromium. Open the page in any browser to see its answer.
- **Fonts** (`fonttest.html`): the page draws every character and compares
  it with a missing glyph's box, so it measures any device it is opened on.
  macOS draws all of the alphabet's Ethiopic and Canadian syllabics. A Linux
  system with DejaVu alone draws its Latin, Greek and Cyrillic, and needs a
  font such as Noto for Ethiopic and Canadian syllabics.
- **GitHub** counts a status description's 140 characters in code points and
  stores 2- and 3-byte UTF-8 intact.

## Prior work

- **Zooko's z-base-32** (2002), and the design document "human-oriented
  base-32 encoding" (https://philzimmermann.com/docs/human-oriented-base-32-encoding.txt),
  chose an alphabet for people, and argued that an encoder and decoder that
  agree on the data's length in bits should use it to write fewer
  characters. His `zbase62` (Python, 2010) and `zbase32` (Python and C)
  libraries implement that agreement as `b2a_l` and `a2b_l`. Sigil uses the
  agreement too: the length sets the layout and makes truncation an error.
- **qntm's** base2048, base32768 and base65536 pack binary into Unicode for
  services that count characters, and his definition of "safe" code points
  (https://qntm.org/safe) is where this alphabet's rules begin.
- **Bitcoin's base58** removed punctuation so that a double-click selects a
  whole address.
- **Unicode's UTS #39** table of look-alikes defines which characters, and
  which sequences, look alike.

## Reproduce and test

```sh
python3 alphabet/alphabet.py --check          # downloads Unicode 14.0.0's data; alphabet.txt, uppercase.txt and ignored.txt are its output
python3 python/vectors.py --check             # vectors.json and vectors.tsv are the reference's output
python3 python/test.py [BLAKE3_TEST_VECTORS]  # the reference implementation
(cd typescript && tsc -p .) && node typescript/dist/test.js
(cd rust && cargo test && cargo run --release --example bench)
(cd lean && lake build && lake exe tests ../vectors.tsv)   # the specification, with Lean 4.31
```

## License

You may use Sigil under the terms of any of these four Free and Open Source Software licences:

* MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)
* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
* Transitive Grace Period Public License 1.0 ([LICENSE-TGPPL](LICENSE-TGPPL) or https://spdx.org/licenses/TGPPL-1.0.html)
* Bootstrap Open Source License v1.0 ([LICENSE-BOSL.txt](LICENSE-BOSL.txt))
