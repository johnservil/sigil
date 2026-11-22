import Sigil.Layout

/-! # Facts a round-trip proof is built from

These hold for Sigil 0.2's format and are checked by Lean's kernel, with no `native_decide`: the
alphabet's letters are distinct, never skipped and never hex digits; the handle's hex digits read
back; the marker goes in and comes out; bytes and digits convert back and forth.

The theorem they were first made for, that decoding inverts encoding, was proved for 0.1's format
(at the tag `v0.1.2+5404f5e7b0912b58eb7d34006c7fb5c73cd4ecc7`). It is not proved for 0.2's format
yet: 0.2 is a release on trial, and its proofs wait until the format settles. -/

namespace Sigil

/-! ## The alphabet -/

/-- Whether a list ascends strictly. -/
def ascending : List Nat → Bool
  | a :: b :: r => a < b && ascending (b :: r)
  | _ => true

theorem alphabet_ascending : ascending alphabet.toList = true := by decide +kernel

theorem alphabet_size : alphabet.size = N := by decide +kernel

theorem alphabet_not_skipped : alphabet.toList.all (fun p => !skipped p) = true := by
  decide +kernel

theorem pairwise_of_ascending : ∀ l : List Nat, ascending l = true → l.Pairwise (· < ·)
  | [] , _ => .nil
  | [_], _ => List.pairwise_singleton _ _
  | a :: b :: r, h => by
    simp only [ascending, Bool.and_eq_true, decide_eq_true_eq] at h
    have ih := pairwise_of_ascending (b :: r) h.2
    refine List.Pairwise.cons ?_ ih
    intro x hx
    cases List.mem_cons.mp hx with
    | inl e => omega
    | inr m => exact Nat.lt_trans h.1 (List.rel_of_pairwise_cons ih m)

/-- In a strictly ascending list, the first index of the `k`-th element is `k`. -/
theorem idxOf?_of_pairwise {l : List Nat} (h : l.Pairwise (· < ·)) (k : Nat) (hk : k < l.length) :
    l.idxOf? l[k] = some k := by
  rw [List.idxOf?_eq_some_iff]
  refine ⟨hk, rfl, fun j hj e => ?_⟩
  have := List.pairwise_iff_getElem.mp h j k (by omega) hk hj
  omega

theorem digit?_alphabet (k : Nat) (hk : k < N) : digit? alphabet[k]! = some k := by
  have hs : k < alphabet.size := by rw [alphabet_size]; exact hk
  have := idxOf?_of_pairwise (pairwise_of_ascending _ alphabet_ascending) k (by simpa using hs)
  rw [getElem!_pos alphabet k hs]
  simp only [digit?, ← Array.getElem_toList, this]

theorem skipped_alphabet (k : Nat) (hk : k < N) : skipped alphabet[k]! = false := by
  have hs : k < alphabet.size := by rw [alphabet_size]; exact hk
  rw [getElem!_pos alphabet k hs]
  have := List.all_eq_true.mp alphabet_not_skipped alphabet[k] (by simp)
  simpa using this

/-! ## The handle -/

/-- The mark before the handle is skipped. -/
theorem leftToRightMark_skipped : skipped leftToRightMark = true := by decide +kernel

/-- No letter is a hex digit, so a sigil's handle ends where its letters begin. -/
theorem alphabet_no_hex : alphabet.toList.all (fun p => (hexValue? p).isNone) = true := by
  decide +kernel

/-- Each lowercase hex digit reads back as its value, and is not skipped. -/
theorem hexValue?_hexDigit : ∀ v, v < 16 →
    hexValue? (hexDigit v) = some v ∧ skipped (hexDigit v) = false := by
  decide +kernel

/-! ## The marker -/

/-- With `H = 2^half`, the marked value's quotient by `H` is `4 · (rest / H) + 1` and its
remainder is `rest mod H`. -/
theorem mark_div_mod (half rest : Nat) :
    mark half rest / 2 ^ half = 4 * (rest / 2 ^ half) + marker ∧
      mark half rest % 2 ^ half = rest % 2 ^ half := by
  have hH := Nat.two_pow_pos half
  have hr := Nat.mod_lt rest hH
  unfold mark
  constructor
  · rw [Nat.mul_comm, Nat.mul_add_div hH, Nat.div_eq_of_lt hr, Nat.add_zero]
  · rw [Nat.mul_comm, Nat.mul_add_mod, Nat.mod_eq_of_lt hr]

/-- The marked value of bits below `2^(2 · half)` is below `2^(2 · half + 2)`. -/
theorem mark_lt (half rest : Nat) (hd : rest < 2 ^ (2 * half)) :
    mark half rest < 2 ^ (2 * half + 2) := by
  have hH := Nat.two_pow_pos half
  have h8 : 2 ^ (2 * half) = 2 ^ half * 2 ^ half := by rw [← Nat.pow_add]; congr 1; omega
  have h82 : 2 ^ (2 * half + 2) = 4 * 2 ^ half * 2 ^ half := by
    rw [Nat.pow_add, h8, show (2 : Nat) ^ 2 = 4 from rfl, Nat.mul_comm, ← Nat.mul_assoc]
  have hq : rest / 2 ^ half < 2 ^ half := by
    rw [Nat.div_lt_iff_lt_mul hH]; rw [h8] at hd; exact hd
  have hr := Nat.mod_lt rest hH
  unfold mark marker
  rw [h82]
  have : (4 * (rest / 2 ^ half) + 1) * 2 ^ half + 2 ^ half ≤ 4 * 2 ^ half * 2 ^ half := by
    rw [← Nat.succ_mul]
    exact Nat.mul_le_mul_right _ (by omega)
  omega

/-- Taking the marker out gives back the bits. -/
theorem unmark_mark (half rest : Nat) : unmark half (mark half rest) = rest := by
  have ⟨hdiv, hmod⟩ := mark_div_mod half rest
  unfold unmark
  rw [Nat.pow_add, show (2 : Nat) ^ 2 = 4 from rfl, ← Nat.div_div_eq_div_mul, hdiv, hmod]
  rw [show (4 * (rest / 2 ^ half) + marker) / 4 = rest / 2 ^ half by unfold marker; omega]
  exact Nat.div_add_mod' rest (2 ^ half)

/-- The marker of a marked value is Sigil's. -/
theorem mark_marker (half rest : Nat) : mark half rest / 2 ^ half % 4 = marker := by
  rw [(mark_div_mod half rest).1]; unfold marker; omega

/-! ## Bytes and digits -/

/-- Induction on a list built from its end. -/
@[elab_as_elim] theorem snoc_induction {α : Type} {motive : List α → Prop} (l : List α)
    (nil : motive []) (snoc : ∀ b x, motive b → motive (b ++ [x])) : motive l := by
  rw [← List.reverse_reverse l]
  induction l.reverse with
  | nil => exact nil
  | cons x r ih => rw [List.reverse_cons]; exact snoc _ _ ih

theorem ofBytes_append (b : List UInt8) (x : UInt8) :
    ofBytes (b ++ [x]) = 256 * ofBytes b + x.toNat := by
  simp [ofBytes, List.foldl_append]

theorem ofBytes_lt (b : List UInt8) : ofBytes b < 2 ^ (8 * b.length) := by
  induction b using snoc_induction with
  | nil => simp [ofBytes]
  | snoc b x ih =>
    rw [ofBytes_append, List.length_append, List.length_singleton, Nat.mul_add, Nat.pow_add]
    have := x.toNat_lt
    have : (2 : Nat) ^ (8 * 1) = 256 := rfl
    omega

theorem toBytes_ofBytes (b : List UInt8) : toBytes (ofBytes b) b.length = b := by
  induction b using snoc_induction with
  | nil => rfl
  | snoc b x ih =>
    rw [ofBytes_append, List.length_append, List.length_singleton, toBytes]
    have hx := x.toNat_lt
    have h1 : (256 * ofBytes b + x.toNat) / 256 = ofBytes b := by omega
    have h2 : (256 * ofBytes b + x.toNat) % 256 = x.toNat := by omega
    rw [h1, h2, ih]
    simp

theorem ofDigits_append (ds : List Nat) (d : Nat) : ofDigits (ds ++ [d]) = N * ofDigits ds + d := by
  simp [ofDigits, List.foldl_append]

theorem toDigits_length (w : Nat) : ∀ n, (toDigits w n).length = n
  | 0 => rfl
  | n + 1 => by simp [toDigits, toDigits_length (w / N) n]

theorem toDigits_lt (w : Nat) : ∀ n, ∀ x ∈ toDigits w n, x < N
  | 0 => by simp [toDigits]
  | n + 1 => by
    intro x hx
    simp only [toDigits, List.mem_append, List.mem_singleton] at hx
    rcases hx with h | h
    · exact toDigits_lt (w / N) n x h
    · subst h; exact Nat.mod_lt _ (by decide)

theorem ofDigits_toDigits (w : Nat) : ∀ n, ofDigits (toDigits w n) = w % N ^ n
  | 0 => by simp [toDigits, ofDigits, Nat.mod_one]
  | n + 1 => by
    rw [toDigits, ofDigits_append, ofDigits_toDigits (w / N) n, Nat.pow_succ, Nat.mul_comm (N ^ n),
      Nat.mod_mul]
    omega

end Sigil
