import Sigil.Blake3
import Sigil.Alphabet

/-! # Sigil: the specification

This file is README.md's "The encoding" in Lean, over the BLAKE3 of `Sigil/Blake3.lean` (C2SP's
specification, `c2sp/BLAKE3/Blake3.lean` of github.com/johnservil/BLAKE3 at commit d4f75f1,
unchanged: SHA-256 ef233d0586e1ba85ea3634be9fefb6721937504579ec50d73b47f300d092fd65, BLAKE3
0d17626c61d735db104858545e5dfc9607704e72b0a6b824e1215254c75db183) and the alphabet that `alphabet/alphabet.py` generates from Unicode's
data (`Sigil/Alphabet.lean`). Data is a list of at least one byte; a sigil is a list of code
points. `Tests.lean` runs it on `vectors.tsv`, the vectors every implementation passes. -/

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

/-- The first `m` from `m₀` at which `target ≤ N^m`, trying at most `fuel` of them. -/
def firstFrom (target : Nat) : (fuel m₀ : Nat) → Nat
  | 0, m => m
  | fuel + 1, m => if target ≤ N ^ m then m else firstFrom target fuel (m + 1)

/-- The fewest characters that hold `8 * L` bits: the least `m` with `2^(8L) ≤ N^m`, found among
`0` to `8L`, since `2^(8L) ≤ N^(8L)`. -/
def fewest (L : Nat) : Nat := firstFrom (2 ^ (8 * L)) (8 * L) 0

/-- `(n, c)` for data of `L` bytes: the sigil's characters, one more than the fewest that hold
`8 * L` bits, and the check's bits, all the room left: the most `c` with `2^(8L + c) ≤ N^n`. -/
def layout (L : Nat) : Nat × Nat :=
  let n := fewest L + 1
  (n, Nat.log2 (N ^ n) - 8 * L)

/-! ## The check -/

/-- BLAKE3's derive-key output of `len` bytes, under context string `context`, for `material`. -/
def deriveKey (context : String) (material : List UInt8) (len : Nat) : List UInt8 :=
  (Blake3.derive_key context.toUTF8 ⟨material.toArray⟩ len).data.toList

/-- The check: the first `c` bits of BLAKE3's derive-key output over the data `d`. -/
def check (d : List UInt8) (c : Nat) : Nat :=
  ofBytes (deriveKey "Sigil 2026-10-22 check" d 8) / 2 ^ (64 - c)

/-! ## Encoding -/

/-- The sigil of `d`, as code points: `w = d · 2^c + check`, written as `n` base-N digits, digit
`k` as `alphabet[k]`. -/
def encode (d : List UInt8) : List Nat :=
  let (n, c) := layout d.length
  let w := ofBytes d * 2 ^ c + check d c
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
  /-- The check fails. -/
  | check
  deriving DecidableEq, Repr

/-- Decoding skips white space and default-ignorable characters (`ignoredRanges`). -/
def ignored (p : Nat) : Bool := ignoredRanges.any fun (a, b) => a ≤ p && p ≤ b

/-- A code point's digit: its place in the alphabet, or a letter's uppercase's place in
`uppercase`. -/
def digit? (p : Nat) : Option Nat := alphabet.idxOf? p <|> uppercase.idxOf? p

/-- The `L` bytes that sigil `s` encodes, or why it encodes none. -/
def decode (s : List Nat) (L : Nat) : Except DecodeError (List UInt8) := do
  let (n, c) := layout L
  let kept := (s.zipIdx 1).filter fun (p, _) => !ignored p
  if kept.length ≠ n then throw (.length kept.length n)
  let ds ← kept.mapM fun (p, i) => match digit? p with
    | some k => pure k
    | none => throw (.character i p)
  let w := ofDigits ds
  if 2 ^ (8 * L + c) ≤ w then throw .range
  let d := toBytes (w / 2 ^ c) L
  if w % 2 ^ c ≠ check d c then throw .check
  pure d

end Sigil
