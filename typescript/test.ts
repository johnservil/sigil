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
  if (encode(data, g.form === "handled") !== g.text) throw new Error(`encode ${g.form} ${g.data}`);
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
if (layout(32).join() !== "22,65519" || layout(8).join() !== "5,2096881") throw new Error("layout");
{
  const g = v.good.find((x: { data: string; form: string }) => x.data.length === 64 && x.form === "handled");
  const chars = Array.from(g.text as string); // the mark, 8 hex digits, then the letters
  // One character uncertain, a letter read three ways, a letter unread or a hex
  // digit unread: the one data comes back (a single change never passes the check).
  for (const [at, choices] of [[13, LETTERS[7] + chars[13] + LETTERS[1500]], [19, ALPHABET], [3, "0123456789abcdef"]] as const) {
    const readings = chars.map((ch, i) => (i === at ? choices : ch));
    if (hex(decodeReadings(readings, 32)) !== g.data) throw new Error(`decodeReadings at ${at}`);
  }
  // The first two letters read two ways each, where the other two also decode (found by the reference).
  const two = chars.map((ch, i) => (i === 9 ? ch + LETTERS[31] : i === 10 ? ch + LETTERS[2031] : ch));
  let kind = "";
  try { decodeReadings(two, 32); } catch (e) { kind = (e as DecodeError).kind; }
  if (kind !== "ambiguous") throw new Error(`decodeReadings, two readings: ${kind}`);
}
console.log(`vectors: ${v.good.length} good, ${v.variants.length} variants and ${v.bad.length} bad agree`);
