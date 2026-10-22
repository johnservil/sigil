import Sigil.Alphabet

/-! # Sigil: the specification

This file is README.md's "The encoding" in Lean, over the alphabet that `alphabet/alphabet.py`
generates from Unicode's data (`Sigil/Alphabet.lean`). Data is a list of at least one byte; a sigil
is a list of code points. `Tests.lean` runs it on `vectors.tsv`, the vectors every implementation
passes, and `Theorems.lean` proves that decoding inverts encoding. -/

namespace Sigil

/-- The alphabet's size. -/
def N : Nat := 1353

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

/-- Whether no `p` from `p₀` divides `k`, for `p` up to `√k`, trying at most `fuel` of them. -/
def noDivisorFrom (k : Nat) : (fuel p₀ : Nat) → Bool
  | 0, _ => true
  | fuel + 1, p => k < p * p || (k % p ≠ 0 && noDivisorFrom k fuel (p + 1))

/-- Whether `k` is prime, by trial division. -/
def isPrime (k : Nat) : Bool := 2 ≤ k && noDivisorFrom k k 2

/-- The largest prime at most `r`, or `0` if there is none. -/
def primeAtMost : Nat → Nat
  | 0 => 0
  | r + 1 => if isPrime (r + 1) then r + 1 else primeAtMost r

/-- The room of `n` characters for data of `L` bytes: `⌊N^n / 2^(8L)⌋`, the factor that `n`
characters leave beside the data. -/
def room (L n : Nat) : Nat := N ^ n / 2 ^ (8 * L)

/-- The first `n` from `n₀` whose room holds a prime larger than `N`, trying at most `fuel`. -/
def firstFrom (L : Nat) : (fuel n₀ : Nat) → Nat
  | 0, n => n
  | fuel + 1, n => if N < primeAtMost (room L n) then n else firstFrom L fuel (n + 1)

/-- `(n, K)` for data of `L` bytes: the sigil's characters, the fewest whose room holds a prime
larger than `N` (found among `0` to `8L + 1`, whose room is at least `N^(8L + 1) / 2^(8L)`), and
`K`, the largest prime at most that room. -/
def layout (L : Nat) : Nat × Nat :=
  let n := firstFrom L (8 * L + 2) 0
  (n, primeAtMost (room L n))

/-! ## Encoding -/

/-- The sigil of `d`, as code points: `w = d · K`, written as `n` base-N digits, digit `k` as
`alphabet[k]`. -/
def encode (d : List UInt8) : List Nat :=
  let (n, K) := layout d.length
  let w := ofBytes d * K
  (toDigits w n).map (alphabet[·]!)

/-! ## Decoding -/

/-- Why a sigil encodes no data of the length asked for. -/
inductive DecodeError where
  /-- `found` characters, where the length asked for takes `expected`. -/
  | length (found expected : Nat)
  /-- The character at `position` (counting from 1, ignored characters included), code point
  `codePoint`, is outside the alphabet. -/
  | character (position codePoint : Nat)
  /-- The value is too large for the length. -/
  | range
  /-- The value is not a multiple of `K`. -/
  | check
  deriving DecidableEq, Repr

/-- Decoding skips white space and default-ignorable characters (`ignoredRanges`). -/
def ignored (p : Nat) : Bool := ignoredRanges.any fun (a, b) => a ≤ p && p ≤ b

/-- A code point's digit: its place in the alphabet, or a letter's uppercase's place in
`uppercase`. -/
def digit? (p : Nat) : Option Nat := alphabet.idxOf? p <|> uppercase.idxOf? p

/-- The `L` bytes that sigil `s` encodes, or why it encodes none. -/
def decode (s : List Nat) (L : Nat) : Except DecodeError (List UInt8) := do
  let (n, K) := layout L
  let kept := (s.zipIdx 1).filter fun (p, _) => !ignored p
  if kept.length ≠ n then throw (.length kept.length n)
  let ds ← kept.mapM fun (p, i) => match digit? p with
    | some k => pure k
    | none => throw (.character i p)
  let w := ofDigits ds
  if K * 2 ^ (8 * L) ≤ w then throw .range
  if w % K ≠ 0 then throw .check
  pure (toBytes (w / K) L)

end Sigil
