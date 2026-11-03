# What a sigil must do, and what it should aim for

A sigil is a short word of Unicode characters that stands for a value of
known length (a hash, a key, an identifier) so that people can copy it,
recognize it and photograph it, and programs can read it back. This page
lists every requirement on the encoding, whatever version: first the
constraints, which every version meets, then the desiderata, which decide
between designs that meet them all, most important first.

The words used here: the **data** is the value, L bytes long; a **word** is
its sigil; a **character** is one thing a person sees in it. Encoder and
decoder both know L, as a program that stores 32-byte hashes does.

## Constraints

**The data**

- **R1. Lossless.** Every value of every length L ≥ 1 has exactly one word,
  and decoding that word gives the value back.
- **R2. The same size however it is counted.** Every word of L bytes has the
  same number of characters, code points, UTF-16 units and terminal cells,
  so no count reveals anything about the data.

**Errors**

- **R3. Every likely mistake is caught.** Decoding fails on any one
  character changed, any two neighbours swapped, any two characters two
  apart swapped, and any character missing or extra. A random string of the
  right length decodes at most once in 2^15 tries, at every length.
- **R4. One unreadable character is recoverable.** Given every candidate
  for one character, exactly one candidate decodes, so a reader unsure of
  one character, or missing it entirely, gets the value back.

**Handling by software**

- **R5. Normalization and case leave a word unchanged.** NFC, NFD, NFKC,
  NFKD and changes of case change no character, so every copy of a word is
  the same bytes, and search boxes, `grep`, databases and git find it.
- **R6. One gesture selects and copies it.** A double-click selects the
  whole word, no line breaks inside it, and it displays in the order it is
  stored, in any paragraph. Its characters are visible, and none joins its
  neighbours or changes their shape.
- **R7. What copying adds, decoding skips.** The decoder drops white space
  and the invisible characters that copying text inserts (soft hyphen,
  zero-width space, word joiner, byte order mark), and refuses every other
  character it does not encode with.
- **R8. Accepted where text is.** Each character is one UTF-16 unit, so
  services that count or store text that way take a word whole.

**People**

- **R9. Drawn.** The default fonts of macOS, iOS, Windows, Android and Linux
  draw every character in a browser, so no word shows a box.
- **R10. Nothing looks alike.** No two characters look alike, and no
  character looks like several in a row, by Unicode's table of look-alikes
  (UTS #39).
- **R11. Never mistaken for hex.** No whole word, of any value, reads as a
  string of hex digits; where a word holds hex on purpose (D2), a reader
  sees where the hex ends. Version 0.1 meets it by an alphabet with no hex
  digit and nothing that looks like one (alphabet/RULES.md, C10). A design
  could admit such letters if something else guarantees it for every
  value, the zero value included, whose word is mostly its alphabet's first
  letter.

**Formats**

- **R12. Its own.** A word of another format, or of a later version that
  marks itself as one, never decodes, and this format's words never decode
  as the other's.

**Secrets and cost**

- **R13. Constant time.** Encoding and decoding take the same time and touch
  the same memory for every value of a length, so a word of a secret leaks
  nothing through timing.
- **R14. Linear.** Time and memory grow in proportion to the data's length.

## Desiderata, most important first

- **D1. Shorter words**, in characters and as they look: more bits in each
  character a person sees, by a larger alphabet, or by marks on letters
  (each mark one that R5 leaves in place: one combining class, never
  composing with its letter).
- **D2. A prefix to speak and type** (Kris and Zooko): the first 28 bits or
  so as hex digits, then letters. A person can say, hear and type the
  prefix (into a search box, to find a commit), and the letters after it
  defeat the common attack of a value that matches another's first 7 hex
  digits. It costs a second character set in one word, and a few more
  characters.
- **D3. Drawn everywhere.** Beyond R9's browsers, the default setups of
  terminals and editors draw every character too (Emacs on macOS, by
  default, drew 5 of 15 scripts as boxes, November 3, 2026).
- **D4. Fewest scripts.** Each script needs its own font, and is one more way
  for a word to show a box; fewer also make a word look even, and leave
  fewer pairs of scripts to check for look-alikes.
- **D5. The ends carry the data.** The first and last characters carry as
  many bits of the value as any other, since people compare words by their
  ends.
- **D6. Oldest characters first.** A character added to Unicode early is
  more likely drawn on platforms nobody has tested: older systems,
  e-readers, PDF tools.
- **D7. Recognized at a glance.** A word looks like nothing else, so a
  reader who meets one knows what it is and what decodes it; and it looks
  worth showing.
- **D8. The same number of UTF-8 bytes** for every word of a preferred size
  (256 bits, say). Low priority.
- **D9. Few UTF-8 bytes.** Lower priority still.

## Left to callers

- **Comparing.** A program comparing two words is safer than an eye: the
  look-alike rule (R10) makes comparing by eye safer, but nobody has
  measured how many characters a person reliably compares.
- **Jumbling.** The data goes into the word in order. A caller whose data is
  built of parts a forger can copy may jumble it first (as F4Jumble does);
  for hashes, keys and random identifiers, jumbling buys nothing.

How version 0.1 meets these: its alphabet's choice is
[alphabet/RULES.md](alphabet/RULES.md), and its encoding is the README's
"The encoding".
