# base345

base345 writes bytes of a known length as one word of letters and digits. A
256-bit hash becomes 32 characters, half the length of hex and never more
bytes, that a double-click selects whole; decoding catches every changed
character.

```
BLAKE3("") in hex      af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            in base64   rxNJufX5oaagQE3qNtzJSZvLJcmtwRK3zJqTyuQfMmI
            in base345  зӆԏƒρҝƥωɿđҙɓʊȝϡʖɖϝԓȸђɑѥџԣъcʞ4ɂӷʦ
```

The 345 characters are the ten digits and lowercase letters of the Latin,
Greek and Cyrillic scripts, whose fonts every major platform ships. Each
takes one or two bytes in UTF-8. A codeword decodes in either case.

## When to use it

base345 serves values that people copy, paste and compare: hashes, keys and
identifiers shown in a status line, a chat, an email or a web page.

| a 256-bit value | characters | bytes in UTF-8 | a double-click selects | a changed character |
|---|---|---|---|---|
| hex | 64 | 64 | the whole value | goes unnoticed |
| base32 | 52 | 52 | the whole value | goes unnoticed |
| base64 | 43 | 43 | part of it, wherever `+`, `/` or `-` falls | goes unnoticed |
| **base345** | **32** | **61 (52 to 64)** | **the whole value** | **is caught** |

Its properties work together:

- **Short.** A base345 hash takes half the characters of hex, and at most as
  many bytes. Two hashes, labelled, fit GitHub's 140-character status
  description.
- **Copied with one gesture.** A double-click selects the whole codeword, and
  copying it carries nothing else. Decoding skips any white space or
  invisible characters that a line break or a copy inserts, and reads
  letters in either case.
- **Checked when decoded.** Every one-character change, every swap of
  neighbours and every truncation fails to decode; any other corruption
  passes about once in 14,000 tries. A damaged copy is reported, and never
  read as a different value.
- **Hard to imitate.** Each character carries 8 bits that someone forging a
  look-alike codeword must match ("Telling codewords apart"), twice what a
  hex character carries.

Other encodings serve other channels:

- **Typed by hand or read aloud:** hex, or z-base-32, whose letters are
  chosen for people to type.
- **Bytes at a premium** (URLs, database columns): base64, at 43 bytes.
- **ASCII only:** hex or base64.

## Use it

Decoding takes the length in bytes that the codeword encodes. The encoder
and decoder agree on it in advance: a 256-bit hash is always 32 bytes.

Python (`python/base345.py`):

```python
import base345
codeword = base345.encode(digest)        # 32 characters for 32 bytes
digest = base345.decode(codeword, 32)    # raises base345.DecodeError
```

TypeScript (`typescript/base345.ts`, in browsers and Node):

```typescript
import { encode, decode, DecodeError } from "base345";
const codeword = encode(digest);          // digest: a Uint8Array
const back = decode(codeword, 32);        // throws DecodeError
```

Rust (`rust/`, no dependencies):

```rust
let codeword = base345::encode(&digest);
let back = base345::decode(&codeword, 32)?;   // Err(DecodeError)
```

A decode error has one of three kinds: `length` (the wrong number of
characters), `character` (one outside the alphabet), and `corrupt` (the
check fails).

## Telling codewords apart

People compare codewords by eye, and often only their first and last few
characters. Someone who wants a codeword that looks like yours cannot choose
a hash's output; they can only try inputs until one encodes to a look-alike.
Each character a person compares makes them match one of the alphabet's
classes of look-alike characters. Unicode's table of look-alikes (UTS #39)
puts base345's 345 characters in 268 classes, so each compared character
costs a forger 8.07 bits, and the first and last four together cost 65
bits. A hex character costs 4 bits, and hex's first and last four cost 32.

The alphabet keeps letters that resemble one another, because that makes
codewords harder to imitate. A look-alike letter enlarges the alphabet, so
codewords get shorter and the check stronger, and it leaves the number of
look-alike classes as it was, so a forger's work per compared character
stays the same. More information in each character, and fewer characters
to compare, make every codeword harder to imitate.

## The encoding

Data of L bytes is a number v below 2^(8L), most significant byte first. Its
codeword is v·K written in base N = 345, with exactly n digits, most
significant first. Digit d is the d-th character of the alphabet
(`alphabet.txt`, in ascending code point order).

- **n** is the fewest digits that leave room for a prime larger than N:
  the smallest n with ⌊N^n / 2^(8L)⌋ > N.
- **K** is the largest prime at most ⌊N^n / 2^(8L)⌋.

Both follow from L alone:

| L (bytes) | 16 | 20 | 32 | 48 | 64 |
|---|---|---|---|---|---|
| n (characters) | 17 | 20 | 32 | 47 | 62 |
| K | 40,829 | 389 | 14,011 | 4,801 | 1,637 |

A decoder told L first drops every character that Unicode 14.0 marks
White_Space or Default_Ignorable_Code_Point (the ranges in `ignored.txt`).
It reads each remaining character as its digit, taking a letter's uppercase
(`uppercase.txt`, in the alphabet's order) as the letter. It requires
exactly n characters, each in the alphabet or its uppercase, whose value w
is a multiple of K with w/K below 2^(8L), and returns w/K as L bytes.

<details>
<summary>Why the check catches what it does</summary>

Multiplying by K makes every codeword's value a multiple of K, and spreads
that property over every digit. Changing one character adds d·N^i for some
0 < |d| < N; swapping neighbours a and b adds (a − b)·N^i·(N − 1). K is a
prime larger than N, so it divides neither, and the result fails the check.
Any other change leaves a multiple of K about once in K tries. This is the
classic arithmetic code of coding theory (an "AN code"); the room for K
costs at most one character.

Knowing the length in advance does two more things. It saves the padding and
end markers other encodings need. And it turns truncation into an error: a
codeword missing a character has the wrong length.
</details>

## The alphabet

`alphabet/alphabet.py` computes the alphabet from Unicode 14.0.0's data
files, by itself: it downloads each file (or reads a saved copy), checks its
SHA-256 and its BLAKE3 before using it, and reads every property from the
files. So the same files give the same alphabet with any Python 3 on any
machine. Each rule keeps the characters that pass it:

| rule | removes | left |
|---|---:|---:|
| at most 2 bytes in UTF-8 (below U+0800) | 1,112,064 | 2,048 |
| assigned (not a surrogate) | 57 | 1,991 |
| assigned by Unicode 5.2 (2009) or earlier | 26 | 1,965 |
| a lowercase letter (general category Ll), or an ASCII digit | 1,391 | 574 |
| left-to-right: a letter of bidi class L, or a digit of class EN | 0 | 574 |
| unchanged by NFC, NFD, NFKC and NFKD | 181 | 393 |
| its uppercase is one character, which lowercases and case-folds back to it | 3 | 390 |
| neither default-ignorable nor white space | 0 | 390 |
| never the second half of a composition | 0 | 390 |
| non-joining (joining type U) | 0 | 390 |
| joins its neighbours into one word (word break ALetter, or Numeric for a digit) | 0 | 390 |
| never a line break beside its neighbours (line break AL, or NU for a digit) | 0 | 390 |
| in Latin, Greek or Cyrillic, whose fonts every major platform ships, or an ASCII digit | 45 | **345** |

<details>
<summary>What each rule protects against</summary>

- **At most 2 bytes in UTF-8.** Every codeword stays within hex's byte count.
- **Unicode 5.2 or earlier.** Fonts lag new letters: DejaVu, a common Linux
  default, lacks the Cyrillic letters that Unicode 6.0 and 7.0 added.
- **Lowercase letters and digits, with uppercase that maps back.** Software
  that changes case leaves a codeword decodable: each letter's uppercase is
  one character that lowercases to it again, and decoding reads either.
- **Left-to-right.** Every character displays in the order it is stored,
  in any paragraph.
- **Unchanged by normalization.** Software normalizes text (older Mac file
  systems to NFD, many web forms to NFC); every character stays itself.
- **No interaction between characters.** The next four rules exclude every
  way two characters can interact: invisible characters, two characters
  normalizing into one, cursive joining, and reordering. Each excludes both
  sides of an interaction, so rules on single characters suffice.
- **One word.** Unicode's word rules (UAX #29) join letters and digits into
  one word, which a double-click selects whole.
- **One line.** Unicode's line rules (UAX #14) allow no break between these
  letters and digits, so a codeword stays on one line.
- **Fonts on every major platform.** A missing glyph shows as a box, and
  boxes hide which character is which. Every major platform ships fonts for
  Latin, Greek and Cyrillic.
</details>

## Evidence

- **The encoding:** all three implementations pass `vectors.json` (or its
  twin, `vectors.tsv`): 220 encodings, 528 variants (copies with white space
  or invisible characters inserted, or letters in uppercase) and 352
  corruptions, each with the error it must give. The Python tests also check
  every one-character change of two codewords (22,016), every swap of
  neighbours in 1,000 codewords (30,912) and every truncation.
- **Selection** (`copytest.html`): a double-click selects whole codewords in
  Chromium. Open the page in any browser to see its answer.
- **Fonts** (`fonttest.html`): the page draws every character and compares it
  with a missing glyph's box, so it measures any device it is opened on.
  Chromium on a Linux system with DejaVu, its default font, draws all 345.
- **GitHub** counts a status description's 140 characters in code points and
  stores 2-byte UTF-8 intact.

## Prior work

- **Zooko's z-base-32** (2002), and the design document "human-oriented
  base-32 encoding" (https://philzimmermann.com/docs/human-oriented-base-32-encoding.txt),
  chose an alphabet for people, and argued that an encoder and decoder that
  agree on the data's length in bits should use it to write fewer
  characters. His `zbase62` (Python, 2010) and `zbase32` (Python and C)
  libraries implement that agreement as `b2a_l` and `a2b_l`. base345 takes
  the same agreement further: it also catches truncation and corruption.
- **qntm's** base2048, base32768 and base65536 pack binary into Unicode for
  services that count characters, and his definition of "safe" code points
  (https://qntm.org/safe) is where this alphabet's rules begin.
- **Bitcoin's base58** removed punctuation so that a double-click selects a
  whole address.

## Reproduce and test

```sh
python3 alphabet/alphabet.py --check          # downloads Unicode 14.0.0's data; alphabet.txt, uppercase.txt and ignored.txt are its output
python3 python/vectors.py --check             # vectors.json and vectors.tsv are the reference's output
python3 python/test.py                        # the reference implementation
(cd typescript && tsc -p .) && node typescript/dist/test.js
(cd rust && cargo test)
```

## License

base345 is yours under either the CC0 1.0 dedication (`LICENSE_CC0`) or the
Apache License 2.0 (`LICENSE_A2`), at your choice.
