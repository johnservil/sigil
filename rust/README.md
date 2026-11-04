# sigilcode

Sigil writes bytes as a sigil: one word that a person can copy with a
double-click, recognize at a glance, and read back from a picture. A 256-bit
hash becomes its first 8 hex digits and 22 letters, no two of which look
alike; in the plain form, 3 letters and the same 22.

> **This is Sigil 0.2, unreleased.** Its sigils and 0.1's never decode as
> each other's.

```
BLAKE3("") in hex    af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
            as a sigil ‎af1349b9ꛥዄपⷉꢦꔾഡꗕᘫꚬꢳꗙᚺᖨꗝᒱᔖৎስसባᗵ
            plain      ᛉᗴᒊꛥዄपⷉꢦꔾഡꗕᘫꚬꢳꗙᚺᖨꗝᒱᔖৎስसባᗵ
```

```rust
let digest = [0xffu8; 32];
let sigil = sigilcode::encode(&digest);              // 8 hex digits and 22 letters
let plain = sigilcode::encode_plain(&digest);        // 3 letters and the same 22
let back = sigilcode::decode(&sigil, 32).unwrap();   // either form; the length in bytes, agreed in advance
assert_eq!(back, digest);
```

- **Hard to misread.** Every misread character, and every swap of neighbours
  or of characters two apart, fails the check, and `decode_readings` recovers
  a letter read several ways, or not read at all.
- **What you see is what decodes.** Decoding skips spaces, line breaks and
  the invisible characters copying inserts, and refuses everything else.
- **Told apart from hex at a glance:** no letter is a hex digit or looks
  like one, so the handle ends where the letters begin.
- **Linear and the same time for any data:** encoding and decoding take
  time and memory in proportion to the data's length, and are built to
  take the same time whatever its value.
- **No dependencies.**

To compare two sigils for security, let a program do it: decode both.

More: [the README](https://github.com/johnservil/sigil#readme), with the
format's specification; [how the alphabet is chosen](https://github.com/johnservil/sigil/blob/main/REQUIREMENTS.md#the-alphabet);
[quality](https://github.com/johnservil/sigil/blob/main/QUALITY.md); and
[the changes](https://github.com/johnservil/sigil/blob/main/CHANGELOG.md).

License: MIT, Apache 2.0, TGPPL 1.0 or BOSL 1.0, at your choice.
