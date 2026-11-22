import Sigil.Alphabet

/-! # Sigil: the specification

This file is README.md's "The encoding" in Lean, over the alphabet that `alphabet/alphabet.py`
generates from Unicode's data and the font tests (`Sigil/Alphabet.lean`). Data is a list of at
least 8 bytes; a sigil is a list of code points: the left-to-right mark, the data's first 8 hex
digits (the handle), and letters for the rest. `Tests.lean` runs it on `vectors.tsv`, the vectors
every implementation passes. -/

namespace Sigil

/-- The alphabet's size: 2^11, so each letter is 11 bits. -/
def N : Nat := 2048

/-! ## Numbers, bytes and digits, the most significant first -/

/-- The number that bytes `b` write, the first byte most significant. -/
def ofBytes (b : List UInt8) : Nat := b.foldl (fun w x => 256 * w + x.toNat) 0

/-- `w` as `L` bytes, the first most significant (`w` mod 256^L). -/
def toBytes (w : Nat) : Nat → List UInt8
  | 0 => []
  | L + 1 => toBytes (w / 256) L ++ [(w % 256).toUInt8]

/-- The number that base-N digits `ds` write, the first most significant. -/
def ofDigits (ds : List Nat) : Nat := ds.foldl (fun w d => N * w + d) 0

/-- `w` as `n` base-N digits, the first most significant (`w` mod N^n). -/
def toDigits (w : Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => toDigits (w / N) n ++ [w % N]

/-- The number that hex digits `hs` write, the first most significant. -/
def ofHex (hs : List Nat) : Nat := hs.foldl (fun w v => 16 * w + v) 0

/-- `w` as `n` hex digits, the first most significant (`w` mod 16^n). -/
def toHex (w : Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => toHex (w / 16) n ++ [w % 16]

/-! ## The layout -/

/-- The handle's hex digits: the data's first 32 bits. -/
def handleDigits : Nat := 8

/-- The data's bits after the handle, for data of `L` bytes (at least 8). -/
def restBits (L : Nat) : Nat := 8 * L - 4 * handleDigits

/-- The letters that carry `b` bits of data: `⌈(b + 14) / 11⌉`, the fewest whose room
`2^(11n − b − 2)` holds a prime larger than `N`. -/
def lettersFor (b : Nat) : Nat := (b + 14 + 10) / 11

/-- The room's exponent: `11n − b − 2`, from 12 to 22. -/
def roomBitsFor (b : Nat) : Nat := 11 * lettersFor b - b - 2

/-- The check prime of each room `2^12` to `2^22`: the largest prime at most the room whose worst
letter distance, from 1 to 63 letters apart, lets through at most twice the changes to two letters
that a random prime would (README.md; computed and checked by `python/sigilcode.py`'s
`check_prime` and the Rust crate's test `ks`). -/
def checkPrimes : List Nat :=
  [4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633]

/-- `(n, K)` for letters that carry `b` bits. -/
def layoutFor (b : Nat) : Nat × Nat := (lettersFor b, checkPrimes.getD (roomBitsFor b - 12) 0)

/-- `(n, K)` for data of `L` bytes: the letters after the handle, and the check prime. -/
def layout (L : Nat) : Nat × Nat := layoutFor (restBits L)

/-! ## Encoding -/

/-- The marker, between the high and low halves of the data's bits after the handle. -/
def marker : Nat := 1

/-- `rest` with the two marker bits between its high and low halves of `half` bits. -/
def mark (half rest : Nat) : Nat := (4 * (rest / 2 ^ half) + marker) * 2 ^ half + rest % 2 ^ half

/-- The rest from a marked value: the marker taken out. -/
def unmark (half m : Nat) : Nat := m / 2 ^ (half + 2) * 2 ^ half + m % 2 ^ half

/-- The number below `K` that makes `h · N^n + m · K + r` a multiple of `K`. -/
def offset (h n K : Nat) : Nat := (K - h * N ^ n % K) % K

/-- U+200E LEFT-TO-RIGHT MARK, a sigil's first code point: it keeps the handle's digits in place
beside right-to-left text. Decoding skips it. -/
def leftToRightMark : Nat := 0x200E

/-- The lowercase hex digit of `v` (below 16), as a code point. -/
def hexDigit (v : Nat) : Nat := if v < 10 then 48 + v else 87 + v

/-- The sigil of `d` (at least 8 bytes), as code points: the mark; the handle `h`, the data's
first 32 bits, as 8 lowercase hex digits; and `t = mark(rest) · K + r` as `n` base-N digits,
digit `k` as `alphabet[k]`. -/
def encode (d : List UInt8) : List Nat :=
  let b := restBits d.length
  let (n, K) := layout d.length
  let h := ofBytes d / 2 ^ b
  let t := mark (b / 2) (ofBytes d % 2 ^ b) * K + offset h n K
  leftToRightMark :: ((toHex h handleDigits).map hexDigit ++ (toDigits t n).map (alphabet[·]!))

/-! ## Decoding -/

/-- Why a sigil encodes no data of the length asked for. -/
inductive DecodeError where
  /-- `found` characters, where the length asked for takes `expected`. -/
  | length (found expected : Nat)
  /-- The character at `position` (counting from 1, skipped characters included), code point
  `codePoint`, is not a hex digit of the handle (`inHandle`) or not a letter of the alphabet. -/
  | character (position codePoint : Nat) (inHandle : Bool)
  /-- `h · N^n + t` is not a multiple of `K`. -/
  | check
  /-- The value is too large for the length. -/
  | range
  /-- The marker is not Sigil's. -/
  | marker
  deriving DecidableEq, Repr

/-- Decoding skips white space, the left-to-right mark and four invisible characters copying
inserts (`skippedRanges`). -/
def skipped (p : Nat) : Bool := skippedRanges.any fun (a, b) => a ≤ p && p ≤ b

/-- A code point's digit: its place in the alphabet. (Over the alphabet as a list, which Lean's
kernel searches in one pass when it checks a particular answer.) -/
def digit? (p : Nat) : Option Nat := alphabet.toList.idxOf? p

/-- A code point's value as a hex digit, in either case. -/
def hexValue? (p : Nat) : Option Nat :=
  if 48 ≤ p ∧ p ≤ 57 then some (p - 48)
  else if 97 ≤ p ∧ p ≤ 102 then some (p - 87)
  else if 65 ≤ p ∧ p ≤ 70 then some (p - 55)
  else none

/-- The `L` bytes (at least 8) that sigil `s` encodes, or why it encodes none. -/
def decode (s : List Nat) (L : Nat) : Except DecodeError (List UInt8) := do
  let b := restBits L
  let (n, K) := layout L
  let kept := (s.zipIdx 1).filter fun (p, _) => !skipped p
  if kept.length ≠ handleDigits + n then throw (.length kept.length (handleDigits + n))
  let hs ← (kept.take handleDigits).mapM fun (p, i) => match hexValue? p with
    | some v => pure v
    | none => throw (.character i p true)
  let ds ← (kept.drop handleDigits).mapM fun (p, i) => match digit? p with
    | some k => pure k
    | none => throw (.character i p false)
  let h := ofHex hs
  let t := ofDigits ds
  if (h * N ^ n + t) % K ≠ 0 then throw .check
  let m := t / K
  if 2 ^ (b + 2) ≤ m then throw .range
  if m / 2 ^ (b / 2) % 4 ≠ marker then throw .marker
  pure (toBytes (h * 2 ^ b + unmark (b / 2) m) L)

end Sigil
