// The TypeScript implementation against vectors.json (run from the repository's root).
import { readFileSync } from "node:fs";
import { blake3Hash, decode, decodeReadings, DecodeError, encode, layout } from "./sigilcode.js";

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
if (layout(32).join() !== "26,14") throw new Error("layout(32)");
{
  const g = v.good.find((x: { data: string }) => x.data.length === 64);
  const chars = Array.from(g.text as string);
  const readings = chars.map((ch, i) => (i === 5 ? "0" + ch + "ab" : ch));
  const found = decodeReadings(readings, 32);
  if (found.length !== 1 || hex(found[0]) !== g.data) throw new Error("decodeReadings");
}
if (hex(blake3Hash(new Uint8Array(0))) !== "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262") throw new Error("BLAKE3");
console.log(`vectors: ${v.good.length} good, ${v.variants.length} variants and ${v.bad.length} bad agree`);
