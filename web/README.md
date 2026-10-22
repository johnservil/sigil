# Play with Sigil

[Open the playground](https://johnservil.github.io/sigil/play.html) to paste
hex bytes, copy their sigil, and decode it back. Try changing one character
in the decoding panel. The sample page also has a reversible hash-display
switch, using the same code as the extension below.

Conversion runs locally in the browser. The page and extension bundle their
Ethiopic and Canadian syllabics fonts, so they need no font-server requests.
Use public data for these experiments; a browser page and other extensions
are outside the Lean proofs' assurance boundary.

## Show hashes as sigils on GitHub and other pages

The experimental extension works in Chrome and Chromium-based browsers:

1. [Download the repository ZIP](https://github.com/johnservil/sigil/archive/refs/heads/main.zip)
   and extract it, or clone the repository.
2. Open `chrome://extensions` and enable **Developer mode**.
3. Click **Load unpacked** and choose the extracted `web/extension` folder.
   The generated files are included; installation needs no build tools.
4. Open a GitHub commit page or another page containing hashes. Pin the
   extension if convenient, then click its toolbar icon.
5. Click it again to restore hex. The badge says **ON** while enabled.

It transforms text in the current page and watches for newly added content
while enabled. Navigation resets it. Browser-internal and other restricted
pages may refuse injection; an **!** badge reports that failure.

- Complete standalone hex strings of 32, 40, 64, 96 or 128 digits become
  sigils. This recognizes hex-shaped text, not the algorithm or authenticity
  of a hash; other identifiers of those lengths can match too.
- Abbreviated commit IDs of 7–12 hex digits become **short sigils** inside
  links whose `/commit/…` or `/commits/…` target starts with that ID.
  Ordinary seven-digit numbers and unlinked short hex remain unchanged.
- Hover a replacement to see the exact original hex and whether it is an
  abbreviation. Double-click to select the sigil. Link destinations remain
  unchanged, so links continue to point at the original resource.
- URLs, attributes, editable fields, buttons, scripts and hidden content
  are left alone. The extension changes main-document text; it does not
  traverse shadow roots or separate frames. A site's font policy can block
  the bundled fonts even while the text conversion works.

**Short sigils preserve short information.** Seven hex digits describe
28 bits. The extension pads one leading zero nibble to make four bytes and
encodes those bytes as five characters. It retains the original spelling
and width for restoration. Decoding the sigil alone returns the padded
bytes: reconstructing the original abbreviation also needs its hex width.
An abbreviation still has the same limitations as the original commit ID;
encoding it does not recover or authenticate the full hash.

Selecting and copying a replacement copies its sigil. Site-provided copy
buttons are not adapted, and tools expecting hex still need hex: toggle
back before copying for those tools. The extension is a display experiment;
a site's own scripts may react to changed text, so restore hex if a page
misbehaves. It makes no security decision about the page.

## Permissions and privacy

The extension requests `activeTab` and `scripting`, giving it temporary
access to the tab the user clicks. It has no persistent host permissions,
telemetry, storage, external scripts or network requests of its own. Local
font files are web-accessible so injected text can use them. Their resource
rule applies to all page origins; it does not grant the extension access to
all pages.

`background.js` installs the bundled font stylesheet and injects
`content.js` on a click. The content script runs in Chrome's isolated world.
It transforms text using DOM text nodes, retaining original spellings for
restoration. A `MutationObserver` handles added text; there is no polling.

## Build and test

The browser uses the existing TypeScript implementation. These files are
source:

- `typescript/{alphabet,sigilcode}.ts`: alphabet and codec.
- `web/page.js`: reversible DOM transformation.
- `web/play.js`, `web/play.css`, `play.html`: playground.
- `web/extension/{manifest.json,background.js}`: extension shell.
- `web/fonts.css` and `web/fonts/`: local Noto fonts and their SIL OFL 1.1
  notices. `web/fonts/manifest.json` records download URLs and both SHA-256
  and BLAKE3 digests.

Regenerate after changing the codec, page transformation or font assets:

```sh
# With TypeScript 5.9.3 installed:
tsc -p typescript
python3 tools/build-web.py
python3 tools/build-web.py --check
node typescript/dist/test.js
python3 tools/test-web.py  # Chromium on PATH
```

The generator bundles the compiled codec into `web/sigilcode.js` and combines
it with the page transformer in `web/extension/content.js`. It also copies
the verified font assets, font stylesheet and project licenses into the
extension folder. It checks both font digests using the alphabet generator's
existing BLAKE3 implementation. No separate browser encoder is maintained.

The Chromium tests check all shared vectors through the generated bundle,
replacement/restoration, short IDs, untouched fields and links, dynamically
added content, repeated content-script injection, and the playground UI.
They exercise the content script in a page, font loading, and the extension
shell against mocked Chrome APIs. Installation and permission granting
through the browser's extension UI are separate manual checks.
