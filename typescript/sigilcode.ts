// Sigil: bytes of a known length written as a sigil, one word of letters and
// digits that a double-click selects whole, with no two characters alike, and
// a check that confirms a reading or picks the right one of several.
// The specification is README.md ("The encoding"); python/sigilcode.py is the
// reference implementation, and vectors.json the tests every implementation
// passes. The data is written in order, unjumbled; README.md's "Why Sigil
// writes the data in order" says why.

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

function isPrime(k: number): boolean {
  if (k < 2) return false;
  for (let p = 2; p * p <= k; p++) if (k % p === 0) return false;
  return true;
}

/** The smallest prime larger than N: K must exceed N (README.md, "Why the
 * check catches what it does"). */
let LEAST_K = N + 1;
while (!isPrime(LEAST_K)) LEAST_K++;

/** [n, K] for data of `length` bytes (at least 1): the sigil's characters,
 * the fewest whose room R = floor(N^n / 2^(8 * length)) holds a prime larger
 * than N, and K, the largest prime at most R. */
export function layout(length: number): [number, number] {
  if (!(Number.isInteger(length) && length >= 1)) throw new RangeError("Sigil encodes at least one byte");
  const bits = BigInt(8 * length);
  let n = 1;
  while (BN ** BigInt(n) >> bits < BigInt(LEAST_K)) n++;
  let k = Number(BN ** BigInt(n) >> bits);
  while (!isPrime(k)) k--;
  return [n, k];
}

const toBig = (b: Uint8Array) => b.reduce((v, byte) => (v << 8n) | BigInt(byte), 0n);

/** `data`'s sigil, layout(data.length)[0] characters of the alphabet.
 * Its protection against look-alikes holds for data that looks random (a
 * secure hash's output, a key, a random identifier): jumble structured data
 * before encoding it (README.md, "Structured data: jumble it first"). */
export function encode(data: Uint8Array): string {
  const [n, k] = layout(data.length);
  let w = toBig(data) * BigInt(k);
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
  const [n, k] = layout(length);
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
  const K = BigInt(k);
  if (w >= K << BigInt(8 * length)) throw new DecodeError("range", `its value is too large for ${length} bytes: a character was misread or changed`);
  if (w % K !== 0n) throw new DecodeError("check", "the check fails: a character was misread or changed");
  let v = w / K;
  const data = new Uint8Array(length);
  for (let i = length - 1; i >= 0; i--) {
    data[i] = Number(v & 0xffn);
    v >>= 8n;
  }
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
