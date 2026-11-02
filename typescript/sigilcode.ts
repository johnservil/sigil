// Sigil: bytes of a known length written as a sigil, one word of letters that
// a double-click selects whole, with no two letters alike, and a check that
// confirms a reading or picks the right one of several.
//
// The specification is README.md ("The encoding"); python/sigilcode.py is the
// reference implementation and vectors.json the tests every implementation
// passes. JavaScript's big integers take time that depends on their values;
// for encoding that leaks nothing, use the Rust implementation.
import { ALPHABET, SKIPPED } from "./alphabet.js";

const LETTERS = Array.from(ALPHABET);
export const N = LETTERS.length;
if (N !== 2048) throw new Error("the alphabet must have 2,048 letters");
const DIGIT = new Map(LETTERS.map((c, i) => [c, i]));
const MARKER = 1n;

export class DecodeError extends Error {
  // "length", "character", "check", "range", "marker", or, from decodeReadings, "ambiguous".
  kind: string;
  constructor(kind: string, message: string) {
    super(message);
    this.kind = kind;
  }
}

function isPrime(k: number): boolean {
  if (k < 2) return false;
  for (let p = 2; p * p <= k; p++) if (k % p === 0) return false;
  return true;
}

// The changes (d1, d2) to two letters, each by less than N, that a check by k
// misses when one letter's place is m times the other's: d1 * m + d2 = 0 (mod k).
function escapes(k: number, m: number): number {
  let hits = 0;
  for (let d1 = 1; d1 < N; d1++) {
    const r = Number((-BigInt(d1) * BigInt(m)) % BigInt(k) + BigInt(k)) % k;
    if ((r > 0 && r < N) || r > k - N) hits++;
  }
  return 2 * hits;
}

// K for a room: the largest prime at most it, larger than N, whose worst letter
// distance, 1 to 63 letters apart, lets through at most twice the two-letter
// changes a random multiplier would (README.md, "The encoding").
const CHECK_PRIMES = new Map<number, number>();
function checkPrime(room: number): number {
  const known = CHECK_PRIMES.get(room);
  if (known !== undefined) return known;
  for (let k = room; ; k--) {
    if (k <= N || !isPrime(k)) continue;
    let worst = 0, m = 1;
    for (let dist = 1; dist < 64; dist++) {
      for (let i = 0; i < 11; i++) m = (2 * m) % k;
      worst = Math.max(worst, escapes(k, m));
    }
    if (worst * k <= 2 * (2 * N - 2) ** 2) {
      CHECK_PRIMES.set(room, k);
      return k;
    }
  }
}

// [n, K] for data of `length` bytes (at least 1): n = ceil((8 * length + 14) / 11)
// letters, and K, the check prime of the room 2^(11n - 8 * length - 2).
export function layout(length: number): [number, number] {
  if (!(length >= 1)) throw new Error("Sigil encodes at least one byte");
  const n = Math.ceil((8 * length + 14) / 11);
  return [n, checkPrime(2 ** (11 * n - 8 * length - 2))];
}

const toBig = (data: Uint8Array) => data.reduce((w, b) => (w << 8n) | BigInt(b), 0n);

export function encode(data: Uint8Array): string {
  const [n, k] = layout(data.length);
  const half = BigInt(4 * data.length);
  const d = toBig(data);
  const marked = ((((d >> half) << 2n) | MARKER) << half) | (d & ((1n << half) - 1n));
  const w = marked * BigInt(k);
  const out: string[] = [];
  for (let i = n - 1; i >= 0; i--) out.push(LETTERS[Number((w >> BigInt(11 * i)) & 2047n)]);
  return out.join("");
}

// White space and four invisible characters copying inserts, which decoding skips.
function skipped(ch: string): boolean {
  const p = ch.codePointAt(0)!;
  return SKIPPED.some(([a, b]) => a <= p && p <= b);
}

export function decode(sigil: string, length: number): Uint8Array {
  const [n, k] = layout(length);
  const letters = Array.from(sigil)
    .map((ch, i): [string, number] => [ch, i])
    .filter(([ch]) => !skipped(ch));
  if (letters.length !== n) throw new DecodeError("length", `${letters.length} letters; ${length} bytes take ${n}`);
  let w = 0n;
  for (const [ch, i] of letters) {
    const d = DIGIT.get(ch);
    if (d === undefined)
      throw new DecodeError("character", `character ${i + 1} (U+${ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}) is not a letter of the alphabet`);
    w = (w << 11n) | BigInt(d);
  }
  const K = BigInt(k);
  if (w % K !== 0n) throw new DecodeError("check", "the check fails: a letter was misread or changed");
  const marked = w / K, half = BigInt(4 * length);
  if (marked >> BigInt(8 * length + 2)) throw new DecodeError("range", `its value is too large for ${length} bytes: a letter was misread or changed`);
  if (((marked >> half) & 3n) !== MARKER) throw new DecodeError("marker", "its marker is not Sigil's: a string of another format, or a changed letter");
  let v = ((marked >> (half + 2n)) << half) | (marked & ((1n << half) - 1n));
  const data = new Uint8Array(length);
  for (let i = length - 1; i >= 0; i--) {
    data[i] = Number(v & 0xffn);
    v >>= 8n;
  }
  return data;
}

// The data of `length` bytes that one reading decodes to, for a reader unsure of
// some letters (an OCR tool, say): `readings` gives each letter's possible
// readings, one string a letter, the likeliest first. Throws DecodeError
// "ambiguous" when several readings decode to different data, and the first
// reading's error when none decodes. The work is the product of the readings' counts.
export function decodeReadings(readings: string[], length: number): Uint8Array {
  const options = readings.map((r) => Array.from(r));
  if (options.some((o) => o.length === 0)) return decode(options.filter((o) => o.length).map((o) => o[0]).join(""), length);
  const choice = options.map(() => 0);
  const found = new Map<string, Uint8Array>();
  let firstError: unknown = null;
  for (;;) {
    try {
      const data = decode(choice.map((c, i) => options[i][c]).join(""), length);
      found.set(Array.from(data).join(","), data);
    } catch (e) {
      if (!(e instanceof DecodeError)) throw e;
      firstError = firstError ?? e;
    }
    let i = options.length;
    for (;;) {
      if (i === 0) {
        if (found.size > 1) throw new DecodeError("ambiguous", `${found.size} readings decode, to different data`);
        if (found.size === 0) throw firstError;
        return found.values().next().value as Uint8Array;
      }
      i--;
      if (++choice[i] < options[i].length) break;
      choice[i] = 0;
    }
  }
}
