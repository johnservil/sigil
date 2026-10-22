// Sigil: bytes of a known length written as a sigil, one word of letters and
// digits that a double-click selects whole, with no two characters alike, and
// a check that confirms a reading or picks the right one of several.
// The specification is README.md ("The encoding"); python/sigilcode.py is the
// reference implementation, and vectors.json the tests every implementation
// passes.

import { ALPHABET, IGNORED, UPPERCASE } from "./alphabet.js";

const CHARS: string[] = Array.from(ALPHABET);
export const N = CHARS.length;
if (N !== 1353) throw new Error("the alphabet must have 1,353 characters");
const DIGIT = new Map<string, number>([
  ...Array.from(UPPERCASE).map((c, d): [string, number] => [c, d]),
  ...CHARS.map((c, d): [string, number] => [c, d]),
]);
const BN = BigInt(N);

/** A sigil that encodes no data of the length asked for: `kind` is
 * "length" (the wrong number of characters), "character" (one outside the
 * alphabet), "range" (a value too large for the length), or "check" (the check
 * fails: a character was misread or changed). */
export class DecodeError extends Error {
  constructor(public kind: "length" | "character" | "range" | "check", message: string) {
    super(message);
  }
}

// BLAKE3 (github.com/BLAKE3-team/BLAKE3-specs) and its derive-key mode, which
// the check uses.

const IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
const PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8];
const CHUNK_START = 1, CHUNK_END = 2, PARENT = 4, ROOT = 8, DERIVE_KEY_CONTEXT = 32, DERIVE_KEY_MATERIAL = 64;

function g(s: Uint32Array, a: number, b: number, c: number, d: number, x: number, y: number) {
  s[a] = s[a] + s[b] + x;
  s[d] ^= s[a];
  s[d] = (s[d] >>> 16) | (s[d] << 16);
  s[c] = s[c] + s[d];
  s[b] ^= s[c];
  s[b] = (s[b] >>> 12) | (s[b] << 20);
  s[a] = s[a] + s[b] + y;
  s[d] ^= s[a];
  s[d] = (s[d] >>> 8) | (s[d] << 24);
  s[c] = s[c] + s[d];
  s[b] ^= s[c];
  s[b] = (s[b] >>> 7) | (s[b] << 25);
}

function compress(cv: number[], block: number[], counter: number, blockLen: number, flags: number): number[] {
  const s = new Uint32Array([...cv.slice(0, 8), ...IV.slice(0, 4), counter >>> 0, Math.floor(counter / 2 ** 32), blockLen, flags]);
  let m = block.slice();
  for (let r = 0; r < 7; r++) {
    g(s, 0, 4, 8, 12, m[0], m[1]); g(s, 1, 5, 9, 13, m[2], m[3]);
    g(s, 2, 6, 10, 14, m[4], m[5]); g(s, 3, 7, 11, 15, m[6], m[7]);
    g(s, 0, 5, 10, 15, m[8], m[9]); g(s, 1, 6, 11, 12, m[10], m[11]);
    g(s, 2, 7, 8, 13, m[12], m[13]); g(s, 3, 4, 9, 14, m[14], m[15]);
    if (r < 6) m = PERMUTATION.map((i) => m[i]);
  }
  const out: number[] = [];
  for (let i = 0; i < 8; i++) out.push((s[i] ^ s[i + 8]) >>> 0);
  for (let i = 0; i < 8; i++) out.push((s[i + 8] ^ cv[i]) >>> 0);
  return out;
}

function words(block: Uint8Array): number[] {
  const b = new Uint8Array(64);
  b.set(block);
  return Array.from({ length: 16 }, (_, i) => (b[4 * i] | (b[4 * i + 1] << 8) | (b[4 * i + 2] << 16) | (b[4 * i + 3] << 24)) >>> 0);
}

type Output = [number[], number[], number, number, number];

function blake3(data: Uint8Array, key: number[], flags: number, length: number): Uint8Array {
  const chunk = (c: Uint8Array, counter: number): Output => {
    let cv = key;
    const blocks: Uint8Array[] = [];
    for (let i = 0; i < c.length; i += 64) blocks.push(c.subarray(i, i + 64));
    if (blocks.length === 0) blocks.push(new Uint8Array(0));
    for (let i = 0; ; i++) {
      const f = flags | (i === 0 ? CHUNK_START : 0) | (i === blocks.length - 1 ? CHUNK_END : 0);
      if (i === blocks.length - 1) return [cv, words(blocks[i]), counter, blocks[i].length, f];
      cv = compress(cv, words(blocks[i]), counter, 64, f).slice(0, 8);
    }
  };
  const cvOf = (o: Output) => compress(...o).slice(0, 8);
  const chunks: Uint8Array[] = [];
  for (let i = 0; i < data.length; i += 1024) chunks.push(data.subarray(i, i + 1024));
  if (chunks.length === 0) chunks.push(new Uint8Array(0));
  const stack: number[][] = [];
  for (let i = 0; i < chunks.length - 1; i++) {
    let cv = cvOf(chunk(chunks[i], i));
    for (let total = i + 1; (total & 1) === 0; total >>= 1) cv = cvOf([key, [...stack.pop()!, ...cv], 0, 64, flags | PARENT]);
    stack.push(cv);
  }
  let out = chunk(chunks[chunks.length - 1], chunks.length - 1);
  while (stack.length) out = [key, [...stack.pop()!, ...cvOf(out)], 0, 64, flags | PARENT];
  const result = new Uint8Array(Math.ceil(length / 64) * 64);
  for (let counter = 0; counter * 64 < length; counter++) {
    const w = compress(out[0], out[1], counter, out[3], out[4] | ROOT);
    w.forEach((x, i) => {
      for (let j = 0; j < 4; j++) result[64 * counter + 4 * i + j] = (x >>> (8 * j)) & 0xff;
    });
  }
  return result.slice(0, length);
}

export function blake3Hash(data: Uint8Array, length = 32): Uint8Array {
  return blake3(data, IV, 0, length);
}

/** BLAKE3's derive-key mode: `length` bytes from key material under a context string. */
export function blake3DeriveKey(context: string, material: Uint8Array, length = 32): Uint8Array {
  const ck = blake3(new TextEncoder().encode(context), IV, DERIVE_KEY_CONTEXT, 32);
  return blake3(material, words(ck).slice(0, 8), DERIVE_KEY_MATERIAL, length);
}

/** [n, c] for data of `length` bytes (at least 1): the sigil's characters,
 * one more than the fewest that hold 8 * length bits, and the check's bits,
 * all the room left. */
export function layout(length: number): [number, number] {
  if (!(Number.isInteger(length) && length >= 1)) throw new RangeError("Sigil encodes at least one byte");
  const limit = 1n << BigInt(8 * length);
  let m = 1;
  while (BN ** BigInt(m) < limit) m++;
  const n = m + 1;
  const c = (BN ** BigInt(n)).toString(2).length - 1 - 8 * length;
  return [n, c];
}

/** The check: the first c bits of BLAKE3, in derive-key mode, over the data. */
function check(data: Uint8Array, c: number): bigint {
  let x = 0n;
  for (const byte of blake3DeriveKey("Sigil 2026-10-22 check", data, 8)) x = (x << 8n) | BigInt(byte);
  return x >> BigInt(64 - c);
}

const toBig = (b: Uint8Array) => b.reduce((v, byte) => (v << 8n) | BigInt(byte), 0n);

export function encode(data: Uint8Array): string {
  const [n, c] = layout(data.length);
  let w = (toBig(data) << BigInt(c)) | check(data, c);
  const out: string[] = new Array(n);
  for (let i = n - 1; i >= 0; i--) {
    out[i] = CHARS[Number(w % BN)];
    w /= BN;
  }
  return out.join("");
}

/** White space and the default-ignorable characters, which decoding skips. */
function ignored(ch: string): boolean {
  const p = ch.codePointAt(0)!;
  return IGNORED.some(([a, b]) => a <= p && p <= b);
}

export function decode(sigil: string, length: number): Uint8Array {
  const [n, c] = layout(length);
  const chars = Array.from(sigil)
    .map((ch, i): [string, number] => [ch, i])
    .filter(([ch]) => !ignored(ch));
  if (chars.length !== n) throw new DecodeError("length", `${chars.length} characters; ${length} bytes take ${n}`);
  let w = 0n;
  for (const [ch, i] of chars) {
    const d = DIGIT.get(ch);
    if (d === undefined)
      throw new DecodeError("character", `character ${i + 1} (U+${ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}) is not in the alphabet`);
    w = w * BN + BigInt(d);
  }
  if (w >> BigInt(8 * length + c) !== 0n) throw new DecodeError("range", `its value is too large for ${length} bytes: a character was misread or changed`);
  let v = w >> BigInt(c);
  const data = new Uint8Array(length);
  for (let i = length - 1; i >= 0; i--) {
    data[i] = Number(v & 0xffn);
    v >>= 8n;
  }
  if ((w & ((1n << BigInt(c)) - 1n)) !== check(data, c)) throw new DecodeError("check", "the check fails: a character was misread or changed");
  return data;
}

/** Every data of `length` bytes that some reading decodes to, for a reader
 * unsure of some characters (an OCR tool, say): `readings` gives each
 * character's possible readings, one string a character, the likeliest first.
 * One result is the answer; more mean the readings leave the sigil ambiguous. */
export function decodeReadings(readings: string[], length: number): Uint8Array[] {
  const options = readings.map((r) => Array.from(r));
  const found: Uint8Array[] = [];
  const seen = new Set<string>();
  const walk = (i: number, chosen: string) => {
    if (i === options.length) {
      try {
        const data = decode(chosen, length);
        const key = Array.from(data).join(",");
        if (!seen.has(key)) {
          seen.add(key);
          found.push(data);
        }
      } catch (e) {
        if (!(e instanceof DecodeError)) throw e;
      }
      return;
    }
    for (const ch of options[i]) walk(i + 1, chosen + ch);
  };
  walk(0, "");
  return found;
}
