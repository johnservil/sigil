// The TypeScript implementation against vectors.json (run from the repository's root).
import { readFileSync } from "node:fs";
import { decode, DecodeError, encode, layout } from "./base11585.js";

const hex = (b: Uint8Array) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
const bytes = (h: string) => Uint8Array.from(h.match(/../g) ?? [], (x) => parseInt(x, 16));
const v = JSON.parse(readFileSync("vectors.json", "utf-8"));
for (const g of v.good) {
  const data = bytes(g.data);
  if (encode(data) !== g.text) throw new Error(`encode ${g.data}`);
  if (hex(decode(g.text, data.length)) !== g.data) throw new Error(`decode ${g.text}`);
}
for (const g of v.spaced) {
  const data = bytes(g.data);
  if (hex(decode(g.text, data.length)) !== g.data) throw new Error(`decode spaced ${JSON.stringify(g.text)}`);
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
const [n, k] = layout(32);
if (n !== 20 || k !== 16369n) throw new Error("layout(32)");
console.log(`vectors: ${v.good.length} good, ${v.spaced.length} spaced and ${v.bad.length} bad agree`);
