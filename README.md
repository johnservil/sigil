# Sigil

Sigil writes bytes as a sigil: one word that a person can copy with a
double-click, recognize at a glance, and read back from a picture. A 256-bit
hash becomes its first 8 hex digits and 22 letters, no two of which look
alike.

> **This branch is Sigil 0.2, unreleased.** Its sigils and 0.1's never
> decode as each other's. Two forms are on trial: handled, which begins with
> the value's first 8 hex digits, which start with git's short hash, and
> plain, which writes those digits as 3 letters. After them both forms have
> the same letters.

```
BLAKE3("") in hex       af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            in base64    rxNJufX5oaagQE3qNtzJSZvLJcmtwRK3zJqTyuQfMmI
            as a sigil   ‎af1349b9ꛡኾपⷃꢢꔹടꗐᘦꚧꢯꗔᚵᖣꗘᒬᔑৎሱसቝᗰ
            plain        ᛄᗯᒅꛡኾपⷃꢢꔹടꗐᘦꚧꢯꗔᚵᖣꗘᒬᔑৎሱसቝᗰ
```

Its 2,048 letters come from fifteen scripts: Canadian syllabics, Ethiopic,
Vai, Devanagari, Runic, Bamum, Malayalam, Telugu, Sinhala, Gujarati, Oriya,
Saurashtra, Bengali, Tifinagh and Kannada. Every one runs left to right,
has no case, and takes one terminal cell, and Unicode treats a run of them
as one word that never breaks across lines, in every Unicode release since
6.0. None is a hex digit or looks like one, so a sigil's handle ends where
its letters begin, and a whole sigil never reads as hex. A sigil looks like
nothing else in a text, and it looks wonderful.

## Try it

[**Play with Sigil →**](https://johnservil.github.io/sigil/play.html)
Paste hex, try random bytes, copy a sigil, or change a letter and see the
check catch it. Everything runs in your browser.

[**Show GitHub hashes as sigils →**](web/README.md)
Load the experimental browser extension, then click to switch hashes to
sigils and back. A short commit ID stays as it is: it is the handle of its
commit's sigil. Hover a sigil to see the original hex. Links keep their original destinations.

## When to use it

Sigil serves values that people copy, recognize and photograph: hashes, keys
and identifiers in a status line, a chat, an email, a web page or a printout.

| a 256-bit value | characters | bits per character | a double-click selects | a misread character |
|---|---|---|---|---|
| hex | 64 | 4 | the whole value | goes unnoticed |
| base32 | 52 | 5 | the whole value | goes unnoticed |
| base64 | 43 | 6 (`I` `l` `1` and `O` `0` look alike) | part of it, wherever `+`, `/` or `-` falls | goes unnoticed |
| **sigil** | **30: 8 hex digits, 22 letters** (plain: 25 letters) | **4 in the handle, 11 in each letter** | **the whole value** | **is caught, and repaired from a few readings** |

Its properties work together:

- **Spoken and searched by its handle** (Kris Nuttycombe's idea). A sigil
  begins with the first 8 hex digits of its value, which start with the 7 of
  the short hash git prints: one person reads them
  off git and says them on the phone, another types them into a tool that
  shows sigils, and both name the same value.
- **Short.** A sigil takes 30 characters where hex takes 64, so two of
  them, labelled, fit GitHub's 140-character status description.
- **The same size, however you count.** A sigil of a given number of bytes
  always has the same number of characters, code points, UTF-16 units,
  user-perceived characters, terminal cells and bytes of UTF-8: no count
  reveals anything about the data.
- **Copied with one gesture.** A double-click selects the whole sigil, and
  copying it carries nothing else. Decoding skips the white space and
  invisible characters that a line break or a copy inserts, and refuses
  every other character, so what you see is what decodes.
- **Hard to misread.** No two letters look alike, and no letter looks like
  several others in a row, by Unicode's table of look-alikes (UTS #39). Every
  misread character fails the check.
- **Read back by machines.** Fonts on the major systems draw every letter,
  and a check confirms a reading or picks the right one of several
  ("Reading sigils by machine").
- **Recognized at a glance.** A word of glyphs from many scripts at once is
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
  sigil's letters take 3 bytes each in UTF-8: 77 for 256 bits, 75 plain.
- **ASCII only:** hex or base64.

## Ways to use it

| You want to… | Start here |
|---|---|
| See how sigils look and whether they copy cleanly | [Playground](https://johnservil.github.io/sigil/play.html), [selection test](copytest.html), [font test](fonttest.html) |
| Read hashes and abbreviated commit IDs as sigils on a website | [Click-to-toggle browser extension](web/README.md) |
| Put fingerprints in logs, CI status lines, chats, labels or reports | Encode the digest bytes with Rust, Python or TypeScript below; keep the hash algorithm and byte length in the surrounding format |
| Convert values in a shell pipeline or a small script | [Python source](python/sigilcode.py), with the pipeline example below |
| Integrate encoding and decoding into an application | [Rust](rust/) for native applications, [TypeScript](typescript/sigilcode.ts) for browsers and Node, or [Python](python/sigilcode.py) |
| Read a photographed or uncertain value | Pass each letter's possible readings to `decode_readings` |
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

Rust (`rust/`, crate `sigilcode`, no runtime dependencies), in time linear
in the data's length and constant whatever its value:

```rust
let sigil = sigilcode::encode(&digest);        // handled; encode_plain for letters only
let back = sigilcode::decode(&sigil, 32)?;     // either form; Err(DecodeError)
```

Python (`python/sigilcode.py`, the reference implementation):

```python
import sigilcode
sigil = sigilcode.encode(digest)            # 8 hex digits and 22 letters for 32 bytes
plain = sigilcode.encode(digest, handle=False)   # 3 letters, then the same 22
digest = sigilcode.decode(sigil, 32)        # either form; raises sigilcode.DecodeError
digest = sigilcode.decode_readings(readings, 32)   # readings: each letter's possible readings
```

From the repository root, a shell pipeline can encode hex read on stdin:

```sh
printf '%s' af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262 |
  PYTHONPATH=python python3 -c 'import sys, sigilcode; print(sigilcode.encode(bytes.fromhex(sys.stdin.read())))'
```

TypeScript (`typescript/sigilcode.ts`, in browsers and Node):

```typescript
import { encode, decode, decodeReadings, DecodeError } from "sigilcode";
const sigil = encode(digest);               // digest: a Uint8Array; encode(digest, false) is plain
const back = decode(sigil, 32);             // either form; throws DecodeError
```

Python's and JavaScript's big integers take time that depends on their
values; for data whose timing must reveal nothing, use the Rust crate.

**What to encode.** Encode a secure hash's output, a key or a random
identifier as it is. For anything else (a file, a document, a message,
structured data), encode its hash: a secure 256-bit hash keeps the sigil at
30 characters for input of any length. Sigil encodes 8 bytes or more.

<details>
<summary>For experts: structured data that decoding must give back</summary>

Sigil writes the data in order, and its protection against look-alikes holds
for data that looks random. Data built of parts (an address made of several
keys, a payment request) that decoding must give back, and so cannot be
hashed, needs jumbling first: F4Jumble (Zcash's ZIP 316, for 38 to 4,194,368
bytes) or another reviewed cryptographic jumbling construction suited to the
length. Reversibility and bit mixing alone are insufficient: a forger can
solve a linear mix for the bytes they control. "Telling sigils apart" says
why.
</details>

A decode error has one of five kinds: `length` (the wrong number of
characters), `character` (one that is not a hex digit in the handle, or not
a letter of the alphabet after it), `check` (the value fails the check),
`range` (a value too large for the length) and `marker` (a string of another
format). The last three mean a character was misread or changed, or the
string is not Sigil's. `decode_readings` adds
`ambiguous`, when the readings leave several data.

**Showing sigils.** Mark sigils with `translate="no"` on any web page that
shows them: browsers may guess that a page of sigils is in another language
and offer to translate it, which replaces every sigil with question marks.
Fonts give letters different widths, so a page that wants every sigil of a
size equally wide draws each letter in a box of fixed width. A page that shows a
sigil in an element of its own (a result, a field) marks that element
`user-select: all`, so one tap or click selects the sigil and nothing near it. Emacs on macOS
draws Tifinagh, Vai, Bamum and Saurashtra letters as boxes: their fonts are
among macOS's hidden supplemental fonts, which browsers use and Emacs does
not search. Copying them from `/System/Library/Fonts/Supplemental` to
`~/Library/Fonts` fixes it.

## Telling sigils apart

To check that two sigils match, let a program compare them: decode both.
Comparing by eye catches accidents, and Sigil is built to make it as safe as
it can. [REQUIREMENTS.md](REQUIREMENTS.md) says what a user guards against
when values are made to look alike.

- **Every letter counts.** Each is one of 2,048, none of which looks like
  another by Unicode's table, and the first letter after the handle and the
  last carry 11 bits of the data each, like every other. The handle's 8 hex
  digits carry 32 bits: a forger matches a given handle in about 2^32 tries.
- **Hashes and keys look random in every letter.** Someone who wants a sigil
  that looks like yours must produce data whose sigil looks like it: for a
  hash they can only try inputs until one hashes to a look-alike, and for a
  key, generate keys.

How many letters a person can reliably tell apart at a glance has not been
measured, so Sigil makes no claim about what a partial comparison by eye
costs a forger.

<details>
<summary>Why Sigil writes the data in order</summary>

Sigil writes the data's bytes in order, the first bytes in the first
letters, and mixes nothing of its own into them. An encoding could jumble the
data first: a few rounds of a hash over its two halves, as F4Jumble does, so
that every letter depends on every bit. What jumbling would do depends on
what a forger controls:

- **A secure hash's output, a key, a random identifier: nothing.** The
  forger can only try inputs, or generate keys, and every result is random
  in every position, jumbled or not.
- **Data the forger chooses entirely: nothing.** Jumbling is public and
  invertible: the forger writes a jumbled value with the victim's ends and
  runs the rounds backwards.
- **Data built of parts a forger can copy: protection.** Without jumbling,
  the forger keeps the victim's parts at the ends and puts their own in the
  middle, and the ends match for free. With it, any change changes every
  letter, and since the data must still hold the copied parts, the forger
  must try their own part until the ends match.

Most of Sigil's data is the first kind. Jumbling inside Sigil would give
every implementation a hash function, its rounds, their inverse and their
tests, and cost every call several compressions, for data that gains
nothing. So Sigil leaves jumbling to the callers whose data is the third
kind.
</details>

## Reading sigils by machine

A sigil photographed or printed can be read back by optical character
recognition (OCR). Three properties serve it:

- **Every letter is drawn.** The alphabet keeps the letters that every tested
  device drew, so a picture of a sigil shows its letters, never boxes.
- **Nothing looks alike.** No two letters look alike, and no letter looks
  like a sequence of others (as `m` looks like `rn`), by Unicode's table of
  look-alikes (UTS #39).
- **The check confirms a reading.** Every misread letter, and every swap of
  neighbours or of characters two apart, fails the check; a random string
  decodes once in 2^18 tries for a 256-bit value (2^19 plain). A reader
  unsure of a character passes its possible readings to `decode_readings`,
  which returns the data the one valid reading encodes. Exactly one reading
  of a character decodes, so `decode_readings` recovers any one character,
  even one unread altogether, with every letter (or hex digit) tried in its
  place. Several uncertain characters at once may leave several readings
  that decode.

## The encoding

Sigil encodes data of L bytes, L ≥ 8, with its alphabet of N = 2,048 letters
(`alphabet.txt`, in ascending code point order: letter k is digit k), so each
letter carries 11 bits. The **handle** h is the data's first 32 bits; letters
after it carry the other b = 8L − 32 bits, the same letters in both forms.

1. **Mark.** Read the letters' b bits as a number d, and put the two marker
   bits `01` between its high and low halves: m = (4 · d_high + 1) · 2^(b/2)
   + d_low, where d_high is d's top b/2 bits and d_low its low b/2 bits. m has
   b + 2 bits and is never zero.
2. **Layout.** The letters are n = ⌈(b + 14) / 11⌉, the fewest whose room
   2^(11n − b − 2) holds a prime larger than N (2,053 or more). K is the
   largest prime at most that room that lets few two-letter errors through:
   at its worst letter distance, from 1 to 63 letters apart, it misses at
   most twice the changes to two letters that a random prime would
   (`check_prime` in `python/sigilcode.py`; "Why the check catches what it
   does" says why the largest prime alone is not enough).
3. **Write.** t = m · K + r, where r < K makes the number h · 2048^n + t a
   multiple of K: r = (−h · 2048^n) mod K. The letters write t in base 2,048
   with exactly n digits, most significant first.
4. **The handle, in either form.** Handled: U+200E LEFT-TO-RIGHT MARK, then
   h as 8 lowercase hex digits. Plain: 2h + v as 3 letters (33 bits), where
   v is the plain form's version bit, 0 in this version.

| data | 64-bit | 80-bit | 128-bit | 160-bit | 192-bit | 256-bit | 512-bit |
|---|---|---|---|---|---|---|---|
| n (letters after the handle) | 5 | 6 | 10 | 13 | 16 | 22 | 45 |
| K | 2,096,881 | 65,519 | 4,093 | 8,179 | 16,381 | 65,519 | 8,179 |
| handled: characters (with 8 hex digits) | 13 | 14 | 18 | 21 | 24 | 30 | 53 |
| a random string decodes once in | 2^23 | 2^18 | 2^14 | 2^15 | 2^16 | 2^18 | 2^15 |
| plain: letters (with 3 for the handle) | 8 | 9 | 13 | 16 | 19 | 25 | 48 |
| a random string decodes once in | 2^24 | 2^19 | 2^15 | 2^16 | 2^17 | 2^19 | 2^16 |

A decoder told L first drops every character in `skipped.txt`: white space
(Unicode's White_Space, which includes every kind of line break), the soft
hyphen, zero-width space, word joiner and byte order mark, which copying
text can insert, and the left-to-right mark. The first character left tells
the form: a hex digit begins a handle, and hex digits are no letters. The
decoder requires exactly 8 + n characters left (handled) or 3 + n (plain),
else the error is `length`; each a hex digit of either case in the handle
and a letter of the alphabet elsewhere, else `character`; plain, the version
bit v of this version, else `marker`; the number h · 2048^n + t a multiple
of K, else `check`; m = ⌊t / K⌋ below 2^(b + 2), else `range`; and m's
marker bits `01`, else `marker`. The data is h's 32 bits, then m with the
marker taken out.

**The markers.** Sigil 0.1 and 0.2 both use `01`. A handled sigil never
reads as 0.1's, since 0.1 has no hex digits; a 0.1 sigil of 32 bytes has as
many letters as a plain 0.2 one, and decodes as one about once in 2^19. A
format that succeeds Sigil's puts another value there, `10` or `11`, and
then its strings never decode as Sigil's, nor Sigil's as its. The plain
form carries one marker more, its version bit v, beside the handle: a later
version that writes 1 there has plain sigils that never decode as this
one's, whatever their letters. The
value `00` stays unused, so that no format's zero data is a string of the
first letter. In the middle, the marker leaves the first and last letters 11
bits each, where people compare by eye. It also catches, about three times
in four, a cluster of errors that reaches past the middle and escapes the
check of K.

<details>
<summary>Why the check catches what it does</summary>

Writing the word as a multiple of K spreads that property over every
character. Changing one letter adds δ · 2^(11i) for some 0 < |δ| < 2,048;
swapping neighbours a and b adds (a − b) · 2^(11i) · (2^11 − 1), and
swapping letters two apart adds (a − b) · 2^(11i) · (2^22 − 1). Changing one
hex digit of the handle adds δ · 16^j · 2048^n for 0 < |δ| < 16, and swapping
hex digits one or two apart adds (a − b) · 16^j · 2048^n times 15 or 255. K
is a prime larger than 2,048, and 2^11 − 1 = 23 · 89, 2^22 − 1 = 3 · 23 · 89
· 683, 15 = 3 · 5 and 255 = 3 · 5 · 17, so K divides none of these and the
word fails the check. A swap across the handle's end puts a letter among its
digits, which decoding refuses. Any other change leaves a multiple of K about once in K tries,
and then keeps the marker about once in four.

Two changed letters i places apart escape the check when δ1 · 2^(11i) + δ2
is a multiple of K. The largest prime at most a room 2^e is 2^e − c for a
small c, so 2^e ≡ c and, at some distance, the multiplier 2^(11i) modulo K is
c times a small power of two: then many pairs (δ1, δ2) escape, 4,094 of
16.8 million at the worst distance for 256-bit data under K = 2^17 − 1. The
rule for K skips such primes; the K it gives for 256-bit data lets 150
through at its worst distance, near the 128 of a random prime.

Since one letter's possible values differ by less than N, at most one of
them gives a multiple of K, and the same holds for a hex digit's 16: that
is why `decode_readings` recovers any one character.

Knowing the length in advance does two more things. It saves the padding
and end markers other encodings need. And it turns truncation into an error:
a sigil missing a letter has the wrong length.
</details>

## The alphabet

[REQUIREMENTS.md](REQUIREMENTS.md) lists every constraint and desideratum
on a sigil, the encoding's and the alphabet's together, and its section
"The alphabet" gives every step that chooses the 2,048 letters with the
requirement it serves, so you can check whether you agree.
`alphabet/alphabet.py` applies them to the data files of every Unicode
release from 6.0.0 to 18.0.0 and the font tests in `alphabet/font-tests`: it downloads each file (or reads a saved
copy), checks its SHA-256 and its BLAKE3 before using it, and reads every
property from the files. So the same inputs give the same alphabet with any
Python 3 on any machine.

**For a format of your own.** A format whose strings might be mistaken for
Sigil's, or a successor to it, puts another value in the marker (`10` or
`11`) and uses another check prime; then neither format's strings decode as
the other's.

## Evidence

- **The encoding:** all four implementations (Python, Rust, TypeScript and
  the Lean specification) pass `vectors.json` (or its twin, `vectors.tsv`):
  220 encodings, 484 variants (copies with skipped characters inserted) and
  748 errors, each of the kind it must give.
- **The check** (`python/test.py`): in 20 random 256-bit sigils, each of
  the 1,023,500 single changed letters and 939 swaps of letters one or two
  apart fails the check. One unread letter comes back alone every time.
  Over 20,000 random 256-bit sigils, the first and last letters each take all
  2,048 values.
- **A specification in Lean** (`lean/`): "The encoding" as Lean
  definitions, over the alphabet that `alphabet/alphabet.py` writes.
  Lean proves that decoding any data's sigil gives the data back
  (`decode_encode`), its kernel checking every step, and the layout's
  contract: K is a prime above N that fits beside the marked data, in the
  fewest letters. It also proves single-letter-error detection, neighbour and
  two-apart swap detection, and uniqueness of an erased letter, for all
  lengths and positions. Every proof rests on Lean's three standard axioms.
  [Check an answer for yourself](lean/README.md) with explicit byte and
  code-point literals. [Bob's verification checklist](VERIFICATION.md)
  records the properties, proof coverage and reliances he can reduce.
  The Rust refinement and executable-byte proofs remain open.
- **Speed** (`rust/examples/bench.rs`): the Rust encodes a 256-bit value in
  1.3 µs and decodes it in 1.4 µs, in a Linux virtual machine on an Apple
  M4 Max, and takes the same time for all zeros, all ones and random data,
  within 2%.
- **Selection** (`copytest.html`): a double-click selects whole sigils in
  Chromium, and a long press does in Brave on iOS. Open the page in any
  browser to see its answer.
- **Fonts** (`alphabet/font-tests`): every device tested, on macOS, iOS,
  Windows, Android and Linux, in Safari, Chrome, Brave and Firefox, drew
  every letter. Each result is kept as it was sent, beside the page that
  measured it.
  [The font test](https://johnservil.github.io/sigil-candidates/check.html)
  measures any device it is opened on.
- **GitHub** counts a status description's 140 characters in code points and
  stores 3-byte UTF-8 intact.

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
  (https://qntm.org/safe) is where this alphabet's rules begin. Sigil keeps
  base2048's 11 bits a character, its letters chosen for people to tell
  apart: one width, caseless, in common fonts, with no look-alikes or hex
  digits. It adds a check that catches every one-letter change and swap of
  neighbours, and decodes in constant time, for secrets.
- **Bitcoin's base58** removed punctuation so that a double-click selects a
  whole address.
- **Unicode's UTS #39** table of look-alikes defines which characters, and
  which sequences, look alike.

## Reproduce and test

```sh
pypy3 alphabet/alphabet.py --check            # or python3; downloads Unicode's data, 6.0.0 to 18.0.0; alphabet.txt, skipped.txt and the generated Lean and TypeScript are its output
python3 python/vectors.py --check             # vectors.json and vectors.tsv are the reference's output
python3 python/test.py                        # the reference implementation
(cd typescript && tsc -p .) && node typescript/dist/test.js
python3 tools/build-web.py --check           # compiled TypeScript matches the checked-in browser bundles
python3 tools/test-web.py                     # Chromium required
(cd rust && cargo test && cargo run --release --example bench)
(cd lean && lake build && lake exe tests ../vectors.tsv)   # the specification and its proofs, with Lean 4.31
python3 tools/test_certificate.py            # answers checked by Lean's kernel, wrong ones refused
```

## License

You may use Sigil under the terms of any of these four Free and Open Source Software licences:

* MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)
* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
* Transitive Grace Period Public License 1.0 ([LICENSE-TGPPL](LICENSE-TGPPL) or https://spdx.org/licenses/TGPPL-1.0.html)
* Bootstrap Open Source License v1.0 ([LICENSE-BOSL.txt](LICENSE-BOSL.txt))

The Noto fonts bundled in `web/fonts/` and `web/extension/fonts/` are under
SIL Open Font License 1.1; their copyright and license notices accompany them.
