# What a sigil must do, and what it should aim for

A sigil is a short word of Unicode characters that stands for a value of
known length: a hash, a key, an identifier. People copy it, recognize it
and photograph it, and programs read it back. Below are the requirements on
the encoding: first the constraints, which every design meets, then the
desiderata, which decide between designs that meet them all, most important
first.

Terms: the **data** is the value, L bytes long. A **word** is its sigil, and
a **character** is one thing a person sees in it. Encoder and decoder both
know L, as a program that stores 32-byte hashes does.

## Constraints

**The data**

- **R1. Lossless.** Every value of every length L ≥ 1 has one word, and
  decoding that word gives the value back.
- **R2. The same size however it is counted.** Every word of L bytes has the
  same number of characters, code points, UTF-16 units, terminal cells and
  UTF-8 bytes, so no count reveals anything about the data.

**Handling by software**

- **R3. Normalization and case leave a word unchanged.** NFC, NFD, NFKC,
  NFKD and changes of case change no character, so every copy of a word is
  the same bytes, and search boxes, `grep`, databases and git find it.
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
  decodes, the better.
- **D3. A prefix to speak and type** (Kris and Zooko): the first bits as
  hex digits, at least 24 and at most 32, 28 best, then letters. A person
  can say, hear and type the prefix (into a search box, to find a commit),
  and the letters after it defeat the common attack of a value that matches
  another's first hex digits. It costs a second character set in one word,
  and a few more characters.
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
- **D8. The ends carry the data.** The first and last characters carry as
  many bits of the value as any other, since people compare words by their
  ends.
- **D9. Oldest characters first.** A character added to Unicode early is
  more likely drawn on platforms nobody has tested: older systems,
  e-readers, PDF tools.
- **D10. Recognized at a glance.** A word looks like nothing else, so a
  reader who meets one knows what it is and what decodes it; and it looks
  worth showing.
- **D11. Few UTF-8 bytes**, for storage and links that count bytes.

## Left to callers

- **Comparing.** A program comparing two words is safer than an eye:
  characters hard to confuse (D4) make comparing by eye safer, but nobody
  has measured how many characters a person reliably compares.
- **Jumbling.** The data goes into the word in order. A caller whose data is
  built of parts a forger can copy may jumble it first (as F4Jumble does);
  for hashes, keys and random identifiers, jumbling buys nothing.

How version 0.1 meets these: its alphabet's choice is
[alphabet/RULES.md](alphabet/RULES.md), and its encoding is the README's
"The encoding".
