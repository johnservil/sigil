# base1160

base1160 writes bytes of a known length as one word of letters. A 256-bit
hash becomes 27 characters that a double-click selects whole, and decoding
catches every one-letter change.

```
BLAKE3("") in hex       af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            in base64    rxNJufX5oaagQE3qNtzJSZvLJcmtwRK3zJqTyuQfMmI
            in base1160  ᗄᎏጞᐇᔄᘜኗᗯቇቓᢵᎃᐇጤᔉᖅᕕᕘᓜᘌⷔᗵⶖᐗᣕቐነ
```

The letters come from two scripts, Ethiopic and Canadian syllabics, 1,160 in
all. Both run left to right, and Unicode treats a run of them as one word
that never breaks across lines. macOS draws all 1,160; the other platforms
are being measured ("Evidence").

## When to use it

base1160 serves values that people copy and paste: hashes, keys, and
identifiers shown in a status line, a chat, an email, or a web page.

| a 256-bit value | characters | a double-click selects | a changed character |
|---|---|---|---|
| hex | 64 | the whole value | goes unnoticed |
| base32 | 52 | the whole value | goes unnoticed |
| base64 | 43 | part of it, wherever `+`, `/` or `-` falls | goes unnoticed |
| base58 (without Bitcoin's checksum) | 44 | the whole value | goes unnoticed |
| **base1160** | **27** | **the whole value** | **is caught** |

Three of its properties work together:

- **Short where characters are counted.** A commit status, a tweet, or a
  terminal line holds a base1160 hash in under half the room of hex. Two
  hashes, labelled, fit GitHub's 140-character status description.
- **Copied with one gesture.** A double-click selects the whole codeword,
  and copying it carries nothing else. Decoding skips any white space or invisible characters that a line
  break or a copy inserts.
- **Checked when decoded.** Every one-character change, every swap of
  neighbours, and every truncation fails to decode; any other corruption
  passes about once in 475,000 tries. A damaged copy is reported, and never
  read as a different value.

Other encodings serve other channels better:

- **Typed by hand or read aloud:** hex, or z-base-32, whose letters are
  chosen for people to type.
- **Counted in bytes** (file names, URLs, database columns): hex or base64.
  Each base1160 letter is 3 bytes in UTF-8, so a 256-bit codeword is 81
  bytes, beside hex's 64.
- **ASCII only:** hex or base64.

## Use it

Decoding takes the length in bytes that the codeword encodes. The encoder
and decoder agree on it in advance: a 256-bit hash is always 32 bytes.

Python (`python/base1160.py`):

```python
import base1160
codeword = base1160.encode(digest)        # 27 letters for 32 bytes
digest = base1160.decode(codeword, 32)    # raises base1160.DecodeError
```

TypeScript (`typescript/base1160.ts`, in browsers and Node):

```typescript
import { encode, decode, DecodeError } from "base1160";
const codeword = encode(digest);          // digest: a Uint8Array
const back = decode(codeword, 32);        // throws DecodeError
```

Rust (`rust/`, no dependencies):

```rust
let codeword = base1160::encode(&digest);
let back = base1160::decode(&codeword, 32)?;   // Err(DecodeError)
```

A decode error has one of three kinds: `length` (the wrong number of
letters), `character` (one outside the alphabet), and `corrupt` (the check
fails).

## The encoding

Data of L bytes is a number v below 2^(8L), most significant byte first. Its
codeword is v·K written in base N = 1,160, with exactly n digits, most
significant first. Digit d is the d-th character of the alphabet
(`alphabet.txt`, in ascending code point order).

- **n** is the fewest digits that leave room for a prime larger than N:
  the smallest n with ⌊N^n / 2^(8L)⌋ > N.
- **K** is the largest prime at most ⌊N^n / 2^(8L)⌋.

Both follow from L alone:

| L (bytes) | 16 | 20 | 32 | 48 | 64 |
|---|---|---|---|---|---|
| n (letters) | 14 | 17 | 27 | 39 | 52 |
| K | 23,473 | 8,527 | 474,983 | 8,273 | 167,663 |

A decoder told L first drops every character that Unicode 14.0 marks
White_Space or Default_Ignorable_Code_Point (the ranges in `ignored.txt`).
It then requires exactly n characters, each in the alphabet, whose value w
is a multiple of K with w/K below 2^(8L), and returns w/K as L bytes.

<details>
<summary>Why the check catches what it does</summary>

Multiplying by K makes every codeword's value a multiple of K, and spreads
that property over every digit. Changing one character adds d·N^i for some
0 < |d| < N; swapping neighbours a and b adds (a − b)·N^i·(N − 1). K is a
prime larger than N, so it divides neither, and the result fails the check.
Any other change leaves a multiple of K about once in K tries. This is the
classic arithmetic code of coding theory (an "AN code"); the room for K costs
one letter, since 26 letters would hold 256 bits with no check.

Knowing the length in advance does two more things. It saves the padding and
end markers other encodings need. And it turns truncation into an error:
a codeword missing a letter has the wrong length.
</details>

## The alphabet

`alphabet/alphabet.py` computes the alphabet from Unicode 14.0.0's data
files. It checks each file's SHA-256 and BLAKE3 before reading it, so the
same inputs give the same alphabet on any machine. Each rule keeps the
characters that pass it:

| rule | removes | left |
|---|---:|---:|
| in the Basic Multilingual Plane | 1,048,576 | 65,536 |
| assigned (not a surrogate) | 3,470 | 62,066 |
| a caseless letter (general category Lo) | 15,940 | 46,126 |
| strongly left-to-right (bidi class L) | 1,239 | 44,887 |
| unchanged by NFC, NFD, NFKC and NFKD | 11,937 | 32,950 |
| unchanged by lower-casing, upper-casing and case folding | 0 | 32,950 |
| neither default-ignorable nor white space | 2 | 32,948 |
| never the second half of a composition | 48 | 32,900 |
| outside the Hangul jamo | 307 | 32,593 |
| non-joining (joining type U) | 174 | 32,419 |
| outside the logical-order exceptions | 19 | 32,400 |
| a letter that joins its neighbours into one word (word break ALetter) | 28,209 | 4,191 |
| never a line break beside a neighbour of its kind (line break AL) | 1,240 | 2,951 |
| in a script whose fonts every major platform ships | 1,791 | **1,160** |

<details>
<summary>What each rule protects against</summary>

- **The Basic Multilingual Plane.** GitHub refuses 4-byte UTF-8 in status
  descriptions (measured), and characters beyond the plane need surrogate
  pairs in UTF-16, which some software splits.
- **Caseless letters.** Letters survive where symbols and punctuation are
  rewritten or dropped; caseless ones survive software that changes case.
- **Strongly left-to-right.** A right-to-left letter, or a neutral one that
  takes its direction from its neighbours, would make a codeword show in a
  different order from the one it is stored in.
- **Unchanged by normalization and case mapping.** Software normalizes text
  (older Mac file systems to NFD, many web forms to NFC); every alphabet
  letter stays itself under all four forms.
- **The next five rules** exclude every way two characters can interact:
  invisible characters, two characters normalizing into one, syllable
  blocks, cursive joining, and reordering. Each excludes both sides of an
  interaction. So rules on single characters suffice, and no sequence of
  alphabet letters interacts.
- **A letter that joins into one word.** Unicode's word rules (UAX #29) join
  ALetter characters into one word, which a double-click selects whole.
  Browsers split CJK text by dictionary, so a double-click on a codeword of
  ideographs selects one to four of them (measured in Chromium: 1 of 20).
- **Never a line break.** Unicode's line rules (UAX #14) allow no break
  between two AL characters, so a codeword stays on one line.
- **Fonts on every major platform.** A missing glyph shows as a box, and
  boxes make distinct letters look alike. Most scripts that pass the rules
  above lack a font on some platform. Ethiopic and Canadian syllabics have
  them: macOS draws all 1,160 letters (measured), Windows ships Ebrima, Nyala
  and Euphemia, and Android ships Noto fonts for both. `fonttest.html`
  measures any other device.
- **Yi** has fonts on these platforms too, and its letters join into one
  word, but a line may break between two of them (line-break class ID), so
  the line-break rule leaves them out. A word joiner between each pair would
  keep a Yi codeword on one line, at the cost of a second written form for
  every codeword.
</details>

## Evidence

- **The encoding:** all three implementations pass `vectors.json` (or its
  twin, `vectors.tsv`): 220 encodings, 440 codewords with white space or
  invisible characters inserted, and 308 corruptions, each with the error it
  must give. The Python tests also check every one-letter change of two
  codewords (62,586), every swap of neighbours in 1,000 codewords (25,978),
  and every truncation.
- **Selection** (`copytest.html`): a double-click selects the whole codeword
  in Chromium and in Chrome on macOS. Open the page in any browser to see
  its answer; a long-press on a phone is next.
- **Fonts** (`fonttest.html`): Chrome on macOS draws all 1,160 letters. The
  page draws every letter and compares it with a missing glyph's box, so it
  measures any device it is opened on; iOS, Windows and Android are next.
  Fonts can cover a script in part: a Linux VM with few fonts drew 403 of
  the 707 Canadian syllabics, and none of the Ethiopic.
- **GitHub** counts a status description's 140 characters in code points,
  stores 2- and 3-byte UTF-8 intact, and refuses 4-byte UTF-8.

## Prior work

- **Zooko's z-base-32** (2002), and the design document "human-oriented
  base-32 encoding" (https://philzimmermann.com/docs/human-oriented-base-32-encoding.txt),
  chose an alphabet for people, and argued that an encoder and decoder that
  agree on the data's length in bits should use it to write fewer
  characters. His `zbase62` (Python, 2010) and `zbase32` (Python and C)
  libraries implement that agreement as `b2a_l` and `a2b_l`. base1160 takes
  the same agreement further: it also catches truncation and corruption.
- **qntm's** base2048, base32768 and base65536 pack binary into Unicode for
  services that count characters, and his definition of "safe" code points
  (https://qntm.org/safe) is where this alphabet's first rules begin.
- **Bitcoin's base58** removed punctuation so that a double-click selects a
  whole address.

## Reproduce and test

```sh
sh alphabet/fetch.sh DATA                     # Unicode 14.0.0's data files
python3 alphabet/alphabet.py DATA --check     # alphabet.txt and ignored.txt are the rules' output
python3 python/vectors.py --check             # vectors.json and vectors.tsv are the reference's output
python3 python/test.py                        # the reference implementation
(cd typescript && tsc -p .) && node typescript/dist/test.js
(cd rust && cargo test)
```

## License

base1160 is yours under either the CC0 1.0 dedication (`LICENSE_CC0`) or the
Apache License 2.0 (`LICENSE_A2`), at your choice.
