// The TypeScript implementation against vectors.json (run from the repository's root).
import { readFileSync } from "node:fs";
import { ALPHABET } from "./alphabet.js";
const LETTERS = Array.from(ALPHABET);
import { decode, decodeReadings, DecodeError, encode, layout } from "./sigilcode.js";

const hex = (b: Uint8Array) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
const bytes = (h: string) => Uint8Array.from(h.match(/../g) ?? [], (x) => parseInt(x, 16));
const v = JSON.parse(readFileSync("vectors.json", "utf-8"));
for (const g of v.good) {
  const data = bytes(g.data);
  if (encode(data) !== g.text) throw new Error(`encode ${g.data}`);
  if (hex(decode(g.text, data.length)) !== g.data) throw new Error(`decode ${g.text}`);
}
for (const g of v.variants) {
  const data = bytes(g.data);
  if (hex(decode(g.text, data.length)) !== g.data) throw new Error(`decode variant ${JSON.stringify(g.text)}`);
}
for (const b of v.bad) {
  let kind: string | null = null;
  try {
    decode(b.text, b.length);
  } catch (e) {
    if (!(e instanceof DecodeError)) throw e;
    kind = e.kind;
  }
  if (kind !== b.error) throw new Error(`${b.text}: ${kind}, not ${b.error}`);
}
if (layout(32).join() !== "25,131063" || layout(8).join() !== "8,4193633") throw new Error("layout");
{
  const g = v.good.find((x: { data: string }) => x.data.length === 64);
  const letters = Array.from(g.text as string);
  // Letter 5 read three ways, letter 11 unread altogether: the one data comes back.
  const readings = letters.map((ch, i) => (i === 5 ? LETTERS[7] + ch + LETTERS[1500] : i === 11 ? ALPHABET : ch));
  if (hex(decodeReadings(readings, 32)) !== g.data) throw new Error("decodeReadings");
  // Letters 0 and 1 read two ways each, where the other two also decode (found by the reference).
  const two = letters.map((ch, i) => (i === 0 ? ch + LETTERS[63] : i === 1 ? ch + LETTERS[2039] : ch));
  let kind = "";
  try { decodeReadings(two, 32); } catch (e) { kind = (e as DecodeError).kind; }
  if (kind !== "ambiguous") throw new Error(`decodeReadings, two readings: ${kind}`);
}
console.log(`vectors: ${v.good.length} good, ${v.variants.length} variants and ${v.bad.length} bad agree`);
