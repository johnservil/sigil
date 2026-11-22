import Sigil

/-! Run `lake env lean --trust=0 Audit.lean` from this directory to recheck the imported proofs
and inspect their axioms. Expected: subsets of `propext`, `Classical.choice`, `Quot.sound`.
This checks the Lean definitions and proofs; it makes no claim about the Rust executable. -/

#check Sigil.layout_contract
#print axioms Sigil.layout_contract
#print axioms Sigil.digit?_alphabet
#print axioms Sigil.alphabet_no_hex
#print axioms Sigil.hexValue?_hexDigit
#print axioms Sigil.unmark_mark
#print axioms Sigil.toBytes_ofBytes
#print axioms Sigil.ofDigits_toDigits
