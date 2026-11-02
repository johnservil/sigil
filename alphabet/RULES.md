# How the alphabet is chosen

Sigil's alphabet is 2,048 letters of Unicode 14.0.0. This page gives every
rule that chooses them and the reason for each, so you can check whether you
agree with each reason, then run `alphabet/alphabet.py` (or your own program)
to get the same 2,048 letters from Unicode's data files.

Two kinds of rule do the choosing. **Constraints** are what every sigil
guarantees, and no letter may break one. **Goals** decide which of the
letters that pass are kept, in a fixed order of priority.

## Inputs

- Unicode 14.0.0's data files, each checked by its SHA-256 and BLAKE3
  (listed in `alphabet.py`).
- `fonts.txt`: which letters each tested device drew, with the date, system
  and browser of each test, and the GitHub issue that reported it. It comes
  from the test page https://johnservil.github.io/sigil-candidates/check.html,
  which anyone can open to test their own device.
  This is the one input that is a measurement, not Unicode's data.

## Constraints

| | every letter is | so that |
|---|---|---|
| C1 | in the Basic Multilingual Plane (U+0000 to U+FFFF), assigned, not a surrogate | each letter is one UTF-16 unit; GitHub and other services accept it |
| C2 | unchanged by NFC, NFD, NFKC and NFKD (no decomposition, not a Hangul syllable) | software that normalizes text leaves a sigil as it was |
| C3 | a caseless letter (general category Lo) of a named script (not Common or Inherited) | software that changes case leaves a sigil as it was; fonts come by script, and G2 counts scripts |
| C4 | strongly left-to-right (bidi class L) | a sigil displays in the order it is stored, in any paragraph |
| C5 | neither white space nor default-ignorable, never the second half of a composition, non-joining (joining type U) | no letter is invisible, merges with a neighbour, or changes its neighbour's shape |
| C6 | a word letter (word break ALetter) and never a line break beside its neighbours (line break AL) | a double-click selects the whole sigil, and it stays on one line |
| C7 | one terminal cell wide (East Asian Width N) | a sigil of n letters takes n cells in every terminal |
| C8 | three bytes of UTF-8 (U+0800 to U+FFFF) | every sigil of the same size has the same length in bytes, and nothing about its letters shows in its length or in the time spent copying it |
| C9 | one of exactly 2,048 = 2^11 letters | each letter is 11 bits, so encoding and decoding take time and memory linear in the data's length, and run in constant time |
| C10 | not a hex digit (0 to 9, a to f) or a look-alike of one | a sigil and hex never share a character |

What these give together: a sigil of L bytes is always n letters, n code
points, n UTF-16 units, 3n bytes of UTF-8, n user-perceived characters, and
n terminal cells.

## Goals, in order

Each goal decides only among the letters that every constraint and every
earlier goal leaves.

| | goal | what it buys | how it acts |
|---|---|---|---|
| G1 | **Fonts.** Every letter is drawn by the default fonts on macOS, iOS, Windows, Android and Linux. | No sigil shows a box in place of a letter. | A letter stays if `fonts.txt` shows it tested on all five systems and drawn by every device tested. |
| G2 | **Fewest scripts.** | Each script needs its own font, and a script of 50 letters appears in about half of all 256-bit sigils, so each script left out is one less way for many sigils to fail. Fewer font switches also make a sigil look even, and leave fewer pairs of scripts to check for look-alikes. | Whole scripts are taken, the largest first (ties to the script whose first letter is oldest, then by name), until they hold at least 2,048 letters. |
| G3 | **No look-alikes.** Of the letters taken, no two look alike, and none looks like several others in a row, by Unicode's table of look-alikes (UTS #39). | A person comparing sigils by eye can tell every letter from every other. | Within each class of look-alikes, the letter with the lowest code point stays. While a letter looks like a sequence of others, the letter that ends the most such spellings goes. If too few letters remain, the next script is taken and this goal applies again. |
| G4 | **Oldest first.** | An older letter is more likely to have a font on platforms nobody has tested: older systems, e-readers, embedded devices, PDF tools, terminals. | Of the letters left, the 2,048 added to Unicode earliest stay, ties to the lowest code point. |

## Beyond these rules

- **Comparing by eye.** The look-alike rule makes comparing sigils by eye
  safer, but a program comparing them is safer still: decode both, or let
  `b3sum --sigilcode --check` compare them.
- **Translation.** Browsers may guess that a page of sigils is in another
  language and offer to translate it, which replaces every sigil with
  question marks. Mark sigils with `translate="no"` on any page that shows
  them.
- **Width on screen.** Fonts give letters different widths, so a sigil's
  width in pixels varies. A page that draws each letter in a box of fixed
  width shows every sigil of a size at the same width.
