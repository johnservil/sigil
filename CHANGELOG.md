# Changes

## November 2, 2026: sigils no longer use hex digits

Sigil's alphabet dropped the 16 characters that hex uses, `0`–`9` and
`a`–`f`. A sigil and a hex string now never share a character, so you, or
a program, can tell which is which at a glance, at any length.

Every sigil changed with it. The hash of nothing, `BLAKE3("")`, was
`ᕖᣇጎʗƾኖᣊⷈeᑭɨᣫѯᖣቀⷃᣡᗯᕜᑡᔮᣥዲᑮᘜᒬ` and is now
`ᕜዀᎃᔨsᓙᖒᐑᑉᙫᕄǥᣗዄᒤᣞыᣧⷋⶍⶩᓖᕅᖇዥⶑ`. A sigil made before this change won't
decode now.

A 256-bit hash still takes 26 characters, and a mistyped character or two
swapped neighbours are still always caught.

The old alphabet was never released as a package. The first release on
crates.io, `sigilcode` 0.1.0, uses the new one.
