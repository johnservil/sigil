// base11585: bytes of a known length as text, one of 11,585 CJK ideographs a
// character, every one-character error and every swap of neighbours caught.
// The specification is README.md ("The encoding"); python/base11585.py is the
// reference implementation, and vectors.json the tests every implementation
// passes.

import { ALPHABET, IGNORED } from "./alphabet.js";

const CHARS: string[] = Array.from(ALPHABET);
export const N = CHARS.length;
if (N !== 11585) throw new Error("the alphabet must have 11,585 characters");
const DIGIT = new Map<string, number>(CHARS.map((c, d) => [c, d]));
const BN = BigInt(N);

/** A text that encodes no data of the length asked for: `kind` is "length"
 * (the wrong number of characters), "character" (one outside the alphabet),
 * or "corrupt" (the check fails). */
export class DecodeError extends Error {
  constructor(public kind: "length" | "character" | "corrupt", message: string) {
    super(message);
  }
}

function isPrime(k: bigint): boolean {
  if (k < 2n) return false;
  for (let d = 2n; d * d <= k; d++) if (k % d === 0n) return false;
  return true;
}

/** [n, K] for data of `length` bytes (at least 1). */
export function layout(length: number): [number, bigint] {
  if (!(Number.isInteger(length) && length >= 1)) throw new RangeError("base11585 encodes at least one byte");
  const bits = BigInt(8 * length);
  let n = 1;
  while (BN ** BigInt(n) >> bits <= BN) n++;
  let k = BN ** BigInt(n) >> bits;
  while (!isPrime(k)) k--;
  return [n, k];
}

export function encode(data: Uint8Array): string {
  const [n, k] = layout(data.length);
  let w = 0n;
  for (const byte of data) w = (w << 8n) | BigInt(byte);
  w *= k;
  const out: string[] = new Array(n);
  for (let i = n - 1; i >= 0; i--) {
    out[i] = CHARS[Number(w % BN)];
    w /= BN;
  }
  return out.join("");
}

/** White space and the default-ignorable characters, which decoding skips. */
function ignored(c: string): boolean {
  const p = c.codePointAt(0)!;
  return IGNORED.some(([a, b]) => a <= p && p <= b);
}

export function decode(text: string, length: number): Uint8Array {
  const [n, k] = layout(length);
  const chars = Array.from(text)
    .map((c, i): [string, number] => [c, i])
    .filter(([c]) => !ignored(c));
  if (chars.length !== n) throw new DecodeError("length", `${chars.length} characters; ${length} bytes take ${n}`);
  let w = 0n;
  chars.forEach(([c, i]) => {
    const d = DIGIT.get(c);
    if (d === undefined)
      throw new DecodeError("character", `character ${i + 1} (U+${c.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}) is not in the alphabet`);
    w = w * BN + BigInt(d);
  });
  if (w % k !== 0n) throw new DecodeError("corrupt", "the check fails: the text was changed");
  let v = w / k;
  if (v >> BigInt(8 * length) !== 0n) throw new DecodeError("corrupt", "the check fails: the text was changed");
  const out = new Uint8Array(length);
  for (let i = length - 1; i >= 0; i--) {
    out[i] = Number(v & 0xffn);
    v >>= 8n;
  }
  return out;
}
