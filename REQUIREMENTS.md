# What a sigil must do, and what it should aim for

A sigil is a short word of Unicode characters that stands for a value of
known length: a hash, a key, an identifier. People copy it, recognize it
and photograph it, and programs read it back. Below are the requirements on
the encoding: first the constraints, which every design meets, then the
desiderata, which decide between designs that meet them all, most important
first.

Terms: the **data** is the value, L bytes long, at least 8. A **word** is its sigil, and
a **character** is one thing a person sees in it. Encoder and decoder both
know L, as a program that stores 32-byte hashes does. The **handle** is the
data's first 32 bits, at a word's start. A word has one of two **forms**:
handled, whose handle is 8 hex digits a person can say and type (D1), and
plain, whose handle is 3 letters; after the handle both forms have the same
letters. (On this branch both are on trial; Zooko decides whether 0.2 keeps
the plain form.)

## Harms the user guards against: confusion and disclosure

A sigil helps a person tell apart values that chance made; it cannot help
with values an attacker made. Attackers steal from cryptocurrency users this
way all the time. In one pattern, called address poisoning, they make a
value whose word looks like one the victim uses, and wait for the victim to
copy theirs. The attacker chooses the value, so no format prevents this.
Every program that shows, accepts or looks up sigils guards against it, and
its documentation tells its users how. There are two attacks, as against a
hash function:

- **Matching a value the user has**, like a second preimage. The user makes
  V1; the attacker then makes V2, whose word shares V1's handle, or its
  first and last characters. This is the common attack. Each character the
  attacker matches multiplies the work: the handle's 8 hex digits take
  about 2^32 tries, under a second on one GPU for a hash, and each letter
  2^11 more.
- **Making values that match one another**, like a collision. The attacker
  makes two or more values together, whose words look alike, shows the user
  one, and later puts another in its place. Matching a handle this way
  takes about 2^16 tries. It is rare in practice, and that makes it
  dangerous. Users, defenders and security engineers tend to assume it
  away, and a check of a value against the user's own does nothing against
  a pair the attacker made.

So a handle, or any part of a word, finds a value and never proves one:

- **A program that looks a value up by its handle chooses only when exactly
  one value matches.** With more, it shows them all and lets the user
  choose, or asks for more of the value. Git refuses an ambiguous short
  hash, and a git that reads sigils keeps that rule. In D1's example
  this is the duty of the second user's git, since the format cannot
  enforce it.
- **Even one match may be the attacker's**, where the user's own value is
  not among those the program searched. Where a value matters (a payment,
  a signature, a release), the program compares the whole value with one
  from a source the user trusts.
- **Speaking or searching discloses.** A handle said aloud, or typed into
  a search box, tells its 32 bits to whoever hears or logs it, and a whole
  word copied into a chat, a ticket or a log goes wherever they go. What
  that costs depends on what the value unlocks and who learns it; whether
  someone called the value public or secret decides nothing.
- **A program comparing two words is safer than an eye.** Characters hard
  to confuse (D4) make comparing by eye safer, but nobody has measured how
  many characters a person reliably compares.
- **Jumbling is the caller's choice.** The data goes into the word in
  order. A caller whose data is built of parts a forger can copy may
  jumble it first (as F4Jumble does); for hashes, keys and random
  identifiers, jumbling buys nothing. A jumbled value's handle is the hex
  of the jumbled bytes, so it no longer matches what other tools print
  (D1).

## Constraints

**The data**

- **R1. Lossless.** Every value of every length L ≥ 8 has one word in each
  form, the one the encoder writes, and decoding that word gives the value back.
  Decoding also accepts exactly the other spellings that R3 and R5 allow,
  and nothing else. A value shorter than 8 bytes has no sigil.
- **R2. The same size however it is counted.** Every word of L bytes in a
  form has the same number of characters, code points, UTF-16 units, terminal cells and
  UTF-8 bytes, so no count reveals anything about the data.

**Handling by software**

- **R3. Normalization leaves a word unchanged, and case leaves its value.**
  NFC, NFD, NFKC and NFKD change no character, so every copy of a word is
  the same bytes, and search boxes, `grep`, databases and git find it. A
  change of case changes only the handle's hex digits, and the word decodes
  to the same value; the letters have no case. A search for the word as
  written misses a copy whose case someone changed.
- **R4. One gesture selects and copies it.** A double-click selects the
  whole word, no line breaks inside it, and it displays in the order it is
  stored, in any paragraph. Its characters are visible, but for invisible
  marks that keep it in order (D1's handle needs one), and none joins its
  neighbours or changes their shape.
- **R5. What copying adds, decoding skips.** The decoder drops white space
  and the invisible characters that copying text inserts (soft hyphen,
  zero-width space, word joiner, byte order mark), and refuses every other
  character it does not encode with.
- **R6. Accepted where text is.** Each character is one UTF-16 unit, so
  services that count or store text that way take a word whole.

**People and other formats**

- **R7. Drawn.** The default fonts of macOS, iOS, Windows, Android and Linux
  draw every character in a browser, so no word shows a box.
- **R8. Never mistaken for hex.** No whole word, of any value, reads as a
  string of hex digits; where a word holds hex on purpose (D1), a reader
  sees where the hex ends.
- **R9. Its own.** A word of another format, or of a later version that
  marks itself as one, never decodes, and this format's words never decode
  as the other's. A plain word of 32 bytes has as many letters as a 0.1
  word, so a 0.1 word read as plain 0.2 decodes about once in 2^19, where
  its check, its version bit and its marker happen to pass; a handled word
  never does.

**Timing and cost**

- **R10. Constant time.** Encoding and decoding take the same time and touch
  the same memory for every value of a length, so their timing tells an
  observer nothing about the value.
- **R11. Linear.** Time and memory grow in proportion to the data's length.

**Unicode's releases**

- **R12. Stable.** Each character meets R2 to R7 by its properties in every
  Unicode release from 6.0.0 (2010) to the newest, so the next release is
  unlikely to change how a word behaves. Unicode promises that
  normalization never changes; for the other properties, a character's
  record is the evidence. Decoding depends on no release at all: the
  alphabet is a fixed table.

## Desiderata, most important first

- **D1. A handle to speak and type** (Kris Nuttycombe's idea): the word begins
  with the same 8 hex digits that a hex encoding of the data begins with,
  lowercase, then letters that carry the rest of the data. Before the hex
  comes U+200E LEFT-TO-RIGHT MARK, invisible, as the word's first code
  point (R4): a run of digits after right-to-left text otherwise joins it,
  and shows on its far side. The hex runs over the data's bytes in order,
  high digit first, as git, `sha256sum` and `b3sum` print; a caller whose
  tools print a value byte-reversed (as Bitcoin prints transaction IDs)
  passes the bytes in the order shown. So one person can read a commit's
  short hash off unmodified git, which prints 7 digits (some tools 8), and
  say it on the phone; another types it into a git that shows sigils, and
  both name the same commit, since the handle begins with those digits. A
  handle that differed from the hex would be a second short form of one
  value, worse than none. It costs a second character set in one word, and
  five characters for a 32-byte value. It also makes the front of a word
  cheaper to forge: 8 hex digits hold 32 bits, where 8 letters would hold
  88, and people check fronts. The plain form writes the same 32 bits as 3
  letters, and after them both forms have the same letters, so a reader of
  either form recognizes the other's.
- **D2. Shorter words**, in characters and as they look: more bits in each
  character a person sees, by a larger alphabet, or by marks on letters
  that R3 leaves in place.
- **D3. Mistakes detected.** Decoding fails on the likely mistakes: one
  character changed, neighbours swapped, characters two apart swapped, a
  character missing or extra. And a random string of the right length
  rarely decodes. The more mistakes caught, and the rarer a random string
  decodes, the better. Detection comes before correction (D5): the two
  compete with each other, and with D2, for the same characters.
- **D4. Characters hard to confuse.** The fewer characters that look like
  one another, or like several in a row, and the less alike they look, the
  better; Unicode's table of look-alikes (UTS #39) is one measure.
- **D5. Mistakes corrected.** A reader unsure of a character, or missing it
  entirely, still gets the value back; the more errors a design corrects,
  the better.
- **D6. Drawn everywhere.** Beyond R7's browsers, the default setups of
  terminals and editors draw every character too.
- **D7. Fewest scripts.** Each script needs its own font, and is one more way
  for a word to show a box; fewer also make a word look even, and leave
  fewer pairs of scripts to compare for look-alikes.
- **D8. The ends carry the data.** The last characters, and the first
  after the handle, carry as many bits of the value as any other, since
  people compare words by their ends.
- **D9. Oldest characters first.** A character added to Unicode early is
  more likely drawn on platforms nobody has tested: older systems,
  e-readers, PDF tools.
- **D10. Recognized at a glance.** A word looks like nothing else, so a
  reader who meets one knows what it is and what decodes it; and it looks
  worth showing.
- **D11. Heard.** A screen reader speaks each character so that a listener
  could write the word down. Today's voices read the handle and little
  else (macOS's `say` read a sigil's letters as a run of F, E and G).
- **D12. Sorts as its value sorts.** Ordering words by code point, UTF-8
  bytes or UTF-16 units orders them as their values, byte by byte, so a
  database index or a sorted file lists sigils in their values' order.
  The order a person's language sorts by (a file manager's, a
  spreadsheet's) is its own.
- **D13. Few UTF-8 bytes**, for storage and links that count bytes.

## The alphabet

Sigil's letters are computed, so anyone can check each step's reason and
get the same letters: `alphabet/alphabet.py` runs the steps below on two
inputs. Each step tests every letter that the steps before it left, and
names the constraint or desideratum it serves.

- **Unicode's data files** of every release from 6.0.0 to 18.0.0, each
  pinned by its SHA-256 and its BLAKE3 in `alphabet/unicode-files.txt`
  (164 files, about 84 MB).
- **`alphabet/fonts.txt`**, which letters each tested device drew, with
  the date, system and browser of each test and the GitHub issue that
  reported it. It comes from the test page
  https://johnservil.github.io/sigil-candidates/check.html, which anyone
  can open to test their own device, and `tools/import-fonts.py` appends
  each new result. This is the one input that is a measurement.

| step | every letter is | serves |
|---|---|---|
| 1 | in the Basic Multilingual Plane, assigned, not a surrogate | R6 |
| 2 | three bytes of UTF-8 (U+0800 to U+FFFF) | R2 |
| 3 | unchanged by NFC, NFD, NFKC and NFKD (no decomposition, not a Hangul syllable), and never composed with a neighbour | R3 |
| 4 | a letter with no case (general category Lo, no case mappings) | R3 |
| 5 | of a named script (not Common or Inherited): fonts come by script | R7, D7 |
| 6 | strongly left-to-right (bidi class L) | R4 |
| 7 | visible (neither white space nor default-ignorable) and non-joining (joining type U) | R4 |
| 8 | a word letter (word break ALetter) that never allows a line break beside its neighbours (line break AL) | R4 |
| 9 | one terminal cell wide (East Asian Width N) | R2 |
| 10 | all of steps 1 to 9, in every release from 6.0.0 to 18.0.0 | R12 |
| 11 | not a hex digit or a look-alike of one, by Unicode's look-alike table (UTS #39, release 18.0.0) | R8 |
| 12 | drawn by every device in `fonts.txt`, and tested on each of macOS, iOS, Windows, Android and Linux | R7 |

Three more steps choose among the letters left:

- **The size (R10, R11, D2):** the largest power of two that the letters
  left fill once look-alikes go, so each letter is a whole number of bits.
  A size between powers of two needs an encoding in fixed blocks to stay
  linear; at the sizes R7 leaves, that gains 2-4% in length.
- **Fewest scripts, no look-alikes (D7, D4):** whole scripts, the largest
  first (ties to the script whose first letter is oldest, then by name),
  until the letters taken fill the size without look-alikes. Of each class
  of look-alikes the letter with the lowest code point stays; then, while
  a letter looks like a sequence of others, the letter that ends the most
  such spellings goes.
- **Oldest first (D9):** of the letters left, those added to Unicode
  earliest, ties to the lowest code point.

Together these make each letter one code point, one UTF-16 unit, three
bytes of UTF-8, one user-perceived character and one terminal cell. The
script runs under CPython and PyPy alike (`pypy3 alphabet/alphabet.py
--data DIR` takes about 7 seconds, CPython about 50), and `--check`
confirms that the checked-in files are its output. The encoding is the
README's "The encoding".
