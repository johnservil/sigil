import Sigil

/-! Run `lake env lean --trust=0 Audit.lean` from this directory to recheck imported proofs
and inspect their axioms. Expected: subsets of `propext`, `Classical.choice`, `Quot.sound`.
This checks the Lean definitions and proofs; it makes no claim about the Rust executable. -/

#check Sigil.layout_contract
#print axioms Sigil.layout_contract
#check Sigil.decode_encode
#print axioms Sigil.decode_encode
#check Sigil.decode_alphabet_digits
#print axioms Sigil.decode_alphabet_digits
#check Sigil.single_change_decode_rejected
#print axioms Sigil.single_change_decode_rejected
#print axioms Sigil.adjacent_swap_detected
#print axioms Sigil.two_apart_swap_detected
#print axioms Sigil.erased_digit_unique
#print axioms Sigil.KnownAnswers.sequence_32
#print axioms Sigil.KnownAnswers.uppercase_and_ignored
