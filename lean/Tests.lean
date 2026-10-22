import Sigil.Spec

/-! The specification against `vectors.tsv`, the vectors every implementation passes:
`lake exe tests ../vectors.tsv`. -/

open Sigil

def unescape : List Char → List Char
  | '\\' :: 't' :: r => '\t' :: unescape r
  | '\\' :: 'n' :: r => '\n' :: unescape r
  | '\\' :: 'r' :: r => '\r' :: unescape r
  | '\\' :: '\\' :: r => '\\' :: unescape r
  | c :: r => c :: unescape r
  | [] => []

def points (text : String) : List Nat := (unescape text.toList).map (·.toNat)

def hexBytes (h : String) : List UInt8 :=
  let v (c : Char) := if c ≤ '9' then c.toNat - '0'.toNat else c.toNat - 'a'.toNat + 10
  let rec go : List Char → List UInt8
    | a :: b :: r => (16 * v a + v b).toUInt8 :: go r
    | _ => []
  go h.toList

def decodes (s : List Nat) (d : List UInt8) : Bool :=
  match decode s d.length with
  | .ok x => x == d
  | .error _ => false

def kind : DecodeError → String
  | .length .. => "length" | .character .. => "character" | .range => "range" | .check => "check"

/-- The failures of one vector, empty when it passes. -/
def test (line : String) : List String :=
  match line.splitOn "\t" with
  | ["good", data, text] =>
    let d := hexBytes data
    (if encode d = points text then [] else [s!"encode {data}"]) ++
    (if decodes (points text) d then [] else [s!"decode {data}"])
  | ["variant", data, text] =>
    let d := hexBytes data
    if decodes (points text) d then [] else [s!"variant {data}"]
  | ["bad", length, error, text] =>
    match decode (points text) length.toNat! with
    | .error e => if kind e = error then [] else [s!"bad {length} {error}: {kind e}"]
    | .ok _ => [s!"bad {length} {error}: decoded"]
  | _ => [s!"unreadable line: {line}"]

def main (args : List String) : IO UInt32 := do
  let lines := (← IO.FS.readFile args[0]!).splitOn "\n" |>.filter (· ≠ "")
  let failures := lines.flatMap test
  for f in failures.take 20 do IO.println f
  IO.println s!"{lines.length - failures.length} of {lines.length} vectors pass"
  return if failures.isEmpty then 0 else 1
