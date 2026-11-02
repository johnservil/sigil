# Sigil

Sigil writes bytes as a sigil: one word of letters that a person
can copy with a double-click, compare at a glance, and read back from a
picture. A 256-bit hash becomes 26 characters, no two of which look alike.

```
BLAKE3("") in hex    af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            in base64 rxNJufX5oaagQE3qNtzJSZvLJcmtwRK3zJqTyuQfMmI
            as a sigil ᕜዀᎃᔨsᓙᖒᐑᑉᙫᕄǥᣗዄᒤᣞыᣧⷋⶍⶩᓖᕅᖇዥⶑ
```

Its 1,337 characters are letters of five scripts: Latin, Greek, Cyrillic,
Ethiopic and Canadian syllabics. Every one runs left to right, and Unicode
treats a run of them as one word that never breaks across lines. None is a
hex digit, so a sigil and hex are told apart at a glance. A sigil looks like
nothing else in a text, and it looks wonderful.

## Try it

[**Play with Sigil →**](https://johnservil.github.io/sigil/play.html)
Paste hex, try random bytes, copy a sigil, or change a character and see the
check catch it. Everything runs in your browser, with locally bundled fonts.

[**Show GitHub hashes as sigils →**](web/README.md)
Load the experimental browser extension, then click to switch hashes to
sigils and back. Short commit IDs become short sigils too; hover to see the
original hex. Links keep their original destinations.

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

## Ways to use it

| You want to… | Start here |
|---|---|
| See how sigils look and whether they copy cleanly | [Playground](https://johnservil.github.io/sigil/play.html), [selection test](copytest.html), [font test](fonttest.html) |
| Read hashes and abbreviated commit IDs as sigils on a website | [Click-to-toggle browser extension](web/README.md) |
| Put fingerprints in logs, CI status lines, chats, labels or reports | Encode the digest bytes with Python, TypeScript or Rust below; keep the hash algorithm and byte length in the surrounding format |
| Convert values in a shell pipeline or a small script | [Python source](python/sigilcode.py), with the pipeline example below |
| Integrate encoding and decoding into an application | [TypeScript](typescript/sigilcode.ts) for browsers/Node, [Rust](rust/) for native applications, or [Python](python/sigilcode.py) |
| Read a photographed or uncertain value | Supply possible character readings to `decode_readings`; multiple results mean ambiguity |
| Carry structured data, or identify a file or document | Choose hashing or reversible jumbling as described below |
| Independently check a critical answer or inspect the proofs | [Lean checking guide](lean/README.md) and [Bob's properties/reliances checklist](VERIFICATION.md) |

A statically verified native library is the goal of the
[assembly/C-ABI experiment](experiments/static-arm64/README.md). That
experiment currently proves one arithmetic primitive. Complete C encoding
and decoding APIs and an executable-level Sigil proof remain open.

## Use it

The implementations are in this repository, and the Rust one is on
crates.io as [`sigilcode`](https://crates.io/crates/sigilcode). The browser
playground and extension are ready to try from the checked-in files.
[CHANGELOG.md](CHANGELOG.md) says what changed, and when.

Decoding takes the length in bytes that the sigil encodes. The encoder and
decoder agree on it in advance: a 256-bit hash is always 32 bytes.
Anyone can decode a sigil; keep secret data secret after encoding it.

Python (`python/sigilcode.py`):

```python
import sigilcode
sigil = sigilcode.encode(digest)            # 26 characters for 32 bytes
digest = sigilcode.decode(sigil, 32)        # raises sigilcode.DecodeError
found = sigilcode.decode_readings(readings, 32)   # readings: each character's possible readings
```

From the repository root, a shell pipeline can encode hex read on stdin:

```sh
printf '%s' af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262 |
  PYTHONPATH=python python3 -c 'import sys, sigilcode; print(sigilcode.encode(bytes.fromhex(sys.stdin.read())))'
```

TypeScript (`typescript/sigilcode.ts`, in browsers and Node):

```typescript
import { encode, decode, decodeReadings, DecodeError } from "sigilcode";
const sigil = encode(digest);               // digest: a Uint8Array
const back = decode(sigil, 32);             // throws DecodeError
```

Rust (`rust/`, crate `sigilcode`, no runtime dependencies):

```rust
let sigil = sigilcode::encode(&digest);
let back = sigilcode::decode(&sigil, 32)?;  // Err(DecodeError)
```

**Data with structure: hash it, or jumble it.** Sigil writes the data in
order, and its protection against look-alikes holds for data that looks
random. Data with structure (fields, several keys or hashes together, a
counter, a timestamp) needs one step first, chosen by whether the sigil must
carry the data or only identify it:

| your data | do this |
|---|---|
| a secure hash's output, a key, a random identifier | encode it as it is |
| anything the reader has or can fetch (a file, a document, a public key) | **encode its hash** |
| structured data that decoding must give back (an address made of several keys, a payment request) | **jumble it, then encode** |

A secure 256-bit hash protects the fingerprint of data a forger chooses
entirely and keeps its sigil at 26 characters for input of any length; when
in doubt, hash.
Jumbling keeps the data recoverable (anyone can unjumble), and protects data
only where a forger cannot choose all of it. Jumble with F4Jumble (Zcash's
ZIP 316, for 38 to 4,194,368 bytes) or another reviewed cryptographic
jumbling construction suited to the data length. Reversibility and bit
mixing alone are insufficient: a forger can solve a linear mix for the
bytes they control. "Telling sigils apart" says why.

A decode error has one of four kinds: `length` (the wrong number of
characters), `character` (one outside the alphabet), `range` (a value too
large for the length) and `check` (the value fails the check). The last two mean a
character was misread or changed.

## Telling sigils apart

People compare sigils by eye, often only their first and last few
characters. Someone who wants a sigil that looks like yours must produce
data whose sigil looks like it: for a hash, they can only try inputs until
one hashes to a look-alike, and for a key, generate keys. Each character a
person compares makes them match that character exactly, since no two
characters of the alphabet look alike: a chance of 1 in 1,337, or 10.4
bits, approximately, for every compared character. These are capacity
estimates: valid sigils have dependent digits and a restricted first digit,
so the 83-bit estimate for the first and last four is not a proved attack
cost. Fewer characters carry more information per comparison.

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

Most of Sigil's data is the first kind. Jumbling inside Sigil would give
every implementation a BLAKE3, its rounds, their inverse and their tests,
and cost every call four BLAKE3 compressions (0.36 µs of a 0.94 µs encoding
in the Rust, when Sigil had it), for data that gains nothing. So Sigil leaves jumbling to the
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
- **The check confirms a reading.** Every misread character, and every
  swap of neighbours, fails to decode; other errors fail all but once in
  16,433 times for a 256-bit value. A reader unsure of a character passes
  its possible readings to `decode_readings`, which returns the data that
  the one valid reading encodes. Exactly one reading of a character decodes,
  so `decode_readings` recovers any one character, even one unread
  altogether, with every character of the alphabet tried in its place.

## The encoding

Sigil encodes data of L bytes, L ≥ 1, with its alphabet of N = 2,048 letters
(`alphabet.txt`, in ascending code point order: letter k is digit k), so each
letter carries 11 bits.

1. **Mark.** Read the data as a number d of 8L bits, most significant byte
   first, and put the two marker bits `01` between its high and low halves:
   d′ = (4 · d_high + 1) · 2^(4L) + d_low, where d_high is the data's top 4L
   bits and d_low its low 4L bits. d′ has 8L + 2 bits and is never zero.
2. **Layout.** The sigil has n = ⌈(8L + 14) / 11⌉ letters, the fewest whose
   room 2^(11n − 8L − 2) holds a prime larger than N (2,053 or more). K is
   the largest prime at most that room that lets few two-letter errors
   through: at its worst letter distance, from 1 to 63 letters apart, it
   misses at most twice the changes to two letters that a random prime would
   (`check_prime` in `python/sigilcode.py`; "Why the check catches what it
   does" says why the largest prime alone is not enough).
3. **Write.** w = d′ · K, written in base 2,048 with exactly n digits, most
   significant first: each letter is the next 11 bits of w.

| data | 64-bit | 80-bit | 128-bit | 160-bit | 192-bit | 256-bit | 512-bit |
|---|---|---|---|---|---|---|---|
| n (letters) | 8 | 9 | 13 | 16 | 19 | 25 | 48 |
| K | 4,193,633 | 131,063 | 8,179 | 16,381 | 32,749 | 131,063 | 16,381 |
| a random string decodes once in | 2^24 | 2^19 | 2^15 | 2^16 | 2^17 | 2^19 | 2^16 |

A decoder told L first drops every character in `skipped.txt`: white space
(Unicode 14.0's White_Space, which includes every kind of line break) and
the soft hyphen, zero-width space, word joiner and byte order mark, which
copying text can insert. It requires exactly n characters left (else the
error is `length`), each a letter of the alphabet (else `character`), and a
value w that is a multiple of K (else `check`) with w / K below 2^(8L + 2)
(else `range`) and its marker bits `01` (else `marker`). The data is w / K
with the marker taken out.

**The marker.** A format that succeeds Sigil's puts another value there,
`10` or `11`, and then its strings never decode as Sigil's, nor Sigil's as
its. The value `00` stays unused, so that no format's zero data is a string
of the first letter. In the middle, the marker leaves the first and last
letters 11 bits each, where people compare by eye. It also catches, about
three times in four, a cluster of errors that reaches past the middle and
escapes the check of K.

<details>
<summary>Why the check catches what it does</summary>

Multiplying by K makes every sigil's value a multiple of K, and spreads
that property over every letter. Changing one letter adds δ · 2^(11i) for
some 0 < |δ| < 2,048; swapping neighbours a and b adds (a − b) · 2^(11i) ·
(2^11 − 1), and swapping letters two apart adds (a − b) · 2^(11i) · (2^22 −
1). K is a prime larger than 2,048, and 2^11 − 1 = 23 · 89 and
2^22 − 1 = 3 · 23 · 89 · 683, so K divides none of these and the value fails
the check. Any other change leaves a multiple of K about once in K tries,
and then keeps the marker about once in four.

Two changed letters i places apart escape the check when δ1 · 2^(11i) + δ2
is a multiple of K. The largest prime at most a room 2^e is 2^e − c for a
small c, so 2^e ≡ c and, at some distance, the multiplier 2^(11i) modulo K is
c times a small power of two: then many pairs (δ1, δ2) escape, 4,094 of
16.8 million at the worst distance for 256-bit data under K = 2^17 − 1. The
rule for K skips such primes; the K it gives for 256-bit data lets 150
through at its worst distance, near the 128 of a random prime.

Since one letter's possible values differ by less than N, at most one of
them gives a multiple of K: that is why `decode_readings` recovers any one
letter.

Knowing the length in advance does two more things. It saves the padding
and end markers other encodings need. And it turns truncation into an error:
a sigil missing a letter has the wrong length.
</details>

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
| looks like no sequence of the others (UTS #39) | 22 | 1,353 |
| no hex digit (0-9, a-f) or a look-alike of one | 16 | **1,337** |

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
- **No hex digits.** The last rule drops `0`–`9` and `a`–`f`, whose
  look-alikes the earlier rules already removed, so a sigil and hex never
  share a character: a person or a program tells them apart at a glance,
  at any length. Coming last, it leaves the look-alike rules' work as it
  was.
</details>

## Evidence

- **The encoding:** all three implementations pass `vectors.json` (or its
  twin, `vectors.tsv`): 220 encodings, 528 variants (copies with white space
  or invisible characters inserted, or letters in uppercase) and 352 errors,
  each of the kind it must give.
- **The check** (`python/test.py`): in 20 random 256-bit sigils, each of
  the 694,720 single changed characters and 979 swaps of characters one or
  two apart fails to decode. One unread character comes back alone every
  time. At every length to 1,024 bytes, K is a prime above N in the fewest
  characters.
- **A specification in Lean** (`lean/`): "The encoding" as Lean
  definitions, over the alphabet that `alphabet/alphabet.py` writes.
  It passes `vectors.tsv` too. Lean proves that decoding any data's sigil
  gives the data back (`decode_encode`), its kernel checking every step.
  It also proves the layout's prime and size choices, single-digit-error
  detection, neighbour and two-apart swap detection, and uniqueness of an
  erased digit. The single-digit result covers the Lean decoder on
  canonical alphabet text; the arithmetic results cover all lengths and
  positions.
  [Check an answer for yourself](lean/README.md) with explicit byte and
  code-point literals. [Bob's verification checklist](VERIFICATION.md)
  records the properties, proof coverage and reliances he can reduce.
  The Rust refinement and executable-byte proofs remain open.
- **Speed** (`rust/examples/bench.rs`): the Rust encodes a 256-bit value in
  0.18 µs and decodes it in 0.34 µs, in a Linux virtual machine on an Apple
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
python3 python/test.py                        # the reference implementation
(cd typescript && tsc -p .) && node typescript/dist/test.js
python3 tools/build-web.py --check           # compiled TypeScript matches the checked-in browser bundles
python3 tools/test-web.py                     # Chromium required
(cd rust && cargo test && cargo run --release --example bench)
(cd lean && lake build && lake exe tests ../vectors.tsv)   # the specification, with Lean 4.31
```

## License

You may use Sigil under the terms of any of these four Free and Open Source Software licences:

* MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)
* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
* Transitive Grace Period Public License 1.0 ([LICENSE-TGPPL](LICENSE-TGPPL) or https://spdx.org/licenses/TGPPL-1.0.html)
* Bootstrap Open Source License v1.0 ([LICENSE-BOSL.txt](LICENSE-BOSL.txt))

The Noto fonts bundled in `web/fonts/` and `web/extension/fonts/` are under
SIL Open Font License 1.1; their copyright and license notices accompany them.
