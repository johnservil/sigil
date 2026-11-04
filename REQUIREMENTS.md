# What a sigil must do, and what it should aim for

A sigil is a short word of Unicode characters that stands for a value of
known length: a hash, a key, an identifier. People copy it, recognize it
and photograph it, and programs read it back. Below are the requirements on
the encoding: first the constraints, which every design meets, then the
desiderata, which decide between designs that meet them all, most important
first.

Terms: the **data** is the value, L bytes long, at least 8. A **word** is its sigil, and
a **character** is one thing a person sees in it. Encoder and decoder both
know L, as a program that stores 32-byte hashes does. The **handle** is a
word's first characters, hex digits a person can say and type (D3).

## Adversarial confusion: the user's to guard against

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
  attacker matches multiplies the work: the handle's 7 hex digits take
  about 2^28 tries, under a second on one GPU for a hash, and each letter
  2^11 more.
- **Making values that match one another**, like a collision. The attacker
  makes two or more values together, whose words look alike, shows the user
  one, and later puts another in its place. Matching a handle this way
  takes about 2^14 tries. It is rare in practice, and that makes it
  dangerous. Users, defenders and security engineers tend to assume it
  away, and a check of a value against the user's own does nothing against
  a pair the attacker made.

So a handle, or any part of a word, finds a value and never proves one:

- **A program that looks a value up by its handle chooses only when exactly
  one value matches.** With more, it shows them all and lets the user
  choose, or asks for more of the value. Git refuses an ambiguous short
  hash, and a git that reads sigils keeps that rule. In D3's example
  this is the duty of the second user's git, since the format cannot
  enforce it.
- **Even one match may be the attacker's**, where the user's own value is
  not among those the program searched. Where a value matters (a payment,
  a signature, a release), the program compares the whole value with one
  from a source the user trusts.
- **A program comparing two words is safer than an eye.** Characters hard
  to confuse (D4) make comparing by eye safer, but nobody has measured how
  many characters a person reliably compares.
- **Jumbling is the caller's choice.** The data goes into the word in
  order. A caller whose data is built of parts a forger can copy may
  jumble it first (as F4Jumble does); for hashes, keys and random
  identifiers, jumbling buys nothing. A jumbled value's handle is the hex
  of the jumbled bytes, so it no longer matches what other tools print
  (D3).

## Constraints

**The data**

- **R1. Lossless.** Every value of every length L ≥ 8 has one word, the
  one the encoder writes, and decoding that word gives the value back.
  Decoding also accepts exactly the other spellings that R3 and R5 allow,
  and nothing else. A value shorter than 8 bytes has no sigil.
- **R2. The same size however it is counted.** Every word of L bytes has the
  same number of characters, code points, UTF-16 units, terminal cells and
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
  stored, in any paragraph. Its characters are visible, and none joins its
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
  string of hex digits; where a word holds hex on purpose (D3), a reader
  sees where the hex ends.
- **R9. Its own.** A word of another format, or of a later version that
  marks itself as one, never decodes, and this format's words never decode
  as the other's.

**Secrets and cost**

- **R10. Constant time.** Encoding and decoding take the same time and touch
  the same memory for every value of a length, so a word of a secret leaks
  nothing through timing.
- **R11. Linear.** Time and memory grow in proportion to the data's length.

## Desiderata, most important first

- **D1. Shorter words**, in characters and as they look: more bits in each
  character a person sees, by a larger alphabet, or by marks on letters
  that R3 leaves in place.
- **D2. Mistakes detected.** Decoding fails on the likely mistakes: one
  character changed, neighbours swapped, characters two apart swapped, a
  character missing or extra. And a random string of the right length
  rarely decodes. The more mistakes caught, and the rarer a random string
  decodes, the better. Detection comes before correction (D5): the two
  compete with each other, and with D1, for the same characters.
- **D3. A handle to speak and type** (Kris and Zooko): the word begins
  with the same 7 hex digits that a hex encoding of the data begins with,
  lowercase, then letters that carry the rest of the data. The hex runs
  over the data's bytes in order, high digit first, as git, `sha256sum`
  and `b3sum` print; a caller whose tools print a value byte-reversed (as
  Bitcoin prints transaction IDs) passes the bytes in the order shown. So one person
  can read a commit's short hash off unmodified git, which prints those 7
  digits, and say it on the phone; another types it into a git that shows
  sigils, and both name the same commit. A handle that differed from the
  hex would be a second short form of one value, worse than none. It costs
  a second character set in one word, and about four characters for a
  32-byte value. It also makes the front of a word cheaper to forge: 7
  hex digits hold 28 bits, where 7 letters would hold 77, and people check
  fronts.
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
- **D11. Sorts as its value sorts.** Ordering words by code point, UTF-8
  bytes or UTF-16 units orders them as their values, byte by byte, so a
  database index or a sorted file lists sigils in their values' order.
  The order a person's language sorts by (a file manager's, a
  spreadsheet's) is its own.
- **D12. Few UTF-8 bytes**, for storage and links that count bytes.

How version 0.1 meets these: its alphabet's choice is
[alphabet/RULES.md](alphabet/RULES.md), and its encoding is the README's
"The encoding".
