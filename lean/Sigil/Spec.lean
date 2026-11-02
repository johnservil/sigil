import Sigil.Alphabet

/-! # Sigil: the specification

This file is README.md's "The encoding" in Lean, over the alphabet that `alphabet/alphabet.py`
generates from Unicode's data and the font tests (`Sigil/Alphabet.lean`). Data is a list of at
least one byte; a sigil is a list of code points. `Tests.lean` runs it on `vectors.tsv`, the
vectors every implementation passes, and `Theorems.lean` proves that decoding inverts encoding. -/

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

/-! ## The layout -/

/-- The letters of a sigil of `L` bytes: `⌈(8L + 14) / 11⌉`, the fewest whose room
`2^(11n − 8L − 2)` holds a prime larger than `N`. -/
def letters (L : Nat) : Nat := (8 * L + 14 + 10) / 11

/-- The room's exponent: `11n − 8L − 2`, from 12 to 22. -/
def roomBits (L : Nat) : Nat := 11 * letters L - 8 * L - 2

/-- The check prime of each room `2^12` to `2^22`: the largest prime at most the room whose worst
letter distance, from 1 to 63 letters apart, lets through at most twice the changes to two letters
that a random prime would (README.md; computed and checked by `python/sigilcode.py`'s
`check_prime` and the Rust crate's test `ks`). -/
def checkPrimes : List Nat :=
  [4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633]

/-- `(n, K)` for data of `L` bytes. -/
def layout (L : Nat) : Nat × Nat := (letters L, checkPrimes.getD (roomBits L - 12) 0)

/-! ## Encoding -/

/-- The marker, between the data's high and low halves. -/
def marker : Nat := 1

/-- The data's number with the two marker bits between its high and low halves of `4L` bits. -/
def mark (L d : Nat) : Nat := (4 * (d / 2 ^ (4 * L)) + marker) * 2 ^ (4 * L) + d % 2 ^ (4 * L)

/-- The data's number from a marked value: the marker taken out. -/
def unmark (L m : Nat) : Nat := m / 2 ^ (4 * L + 2) * 2 ^ (4 * L) + m % 2 ^ (4 * L)

/-- The sigil of `d`, as code points: `w = mark(d) · K`, written as `n` base-N digits, digit `k` as
`alphabet[k]`. -/
def encode (d : List UInt8) : List Nat :=
  let (n, K) := layout d.length
  let w := mark d.length (ofBytes d) * K
  (toDigits w n).map (alphabet[·]!)

/-! ## Decoding -/

/-- Why a sigil encodes no data of the length asked for. -/
inductive DecodeError where
  /-- `found` letters, where the length asked for takes `expected`. -/
  | length (found expected : Nat)
  /-- The character at `position` (counting from 1, skipped characters included), code point
  `codePoint`, is not a letter of the alphabet. -/
  | character (position codePoint : Nat)
  /-- The value is not a multiple of `K`. -/
  | check
  /-- The value is too large for the length. -/
  | range
  /-- The marker is not Sigil's. -/
  | marker
  deriving DecidableEq, Repr

/-- Decoding skips white space and four invisible characters copying inserts (`skippedRanges`). -/
def skipped (p : Nat) : Bool := skippedRanges.any fun (a, b) => a ≤ p && p ≤ b

/-- A code point's digit: its place in the alphabet. -/
def digit? (p : Nat) : Option Nat := alphabet.idxOf? p

/-- The `L` bytes that sigil `s` encodes, or why it encodes none. -/
def decode (s : List Nat) (L : Nat) : Except DecodeError (List UInt8) := do
  let (n, K) := layout L
  let kept := (s.zipIdx 1).filter fun (p, _) => !skipped p
  if kept.length ≠ n then throw (.length kept.length n)
  let ds ← kept.mapM fun (p, i) => match digit? p with
    | some k => pure k
    | none => throw (.character i p)
  let w := ofDigits ds
  if w % K ≠ 0 then throw .check
  let m := w / K
  if 2 ^ (8 * L + 2) ≤ m then throw .range
  if m / 2 ^ (4 * L) % 4 ≠ marker then throw .marker
  pure (toBytes (unmark L m) L)

end Sigil
