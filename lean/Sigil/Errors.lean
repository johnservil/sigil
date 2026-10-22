import Sigil.Layout

/-! # Error detection by the AN code

These statements concern base-N digits and divisibility by the layout's K. They quantify over
all byte lengths, digit positions and values, independently of a test corpus. The final section
connects divisibility and single-digit rejection to the Lean decoder on canonical alphabet text.
Case variants, ignored characters and the optimized Rust remain separate work.
-/

namespace Sigil

/-- A prime is coprime to every positive natural number smaller than it. -/
theorem Prime.coprime_of_lt {p a : Nat} (hp : Prime p) (ha : 0 < a) (hlt : a < p) :
    Nat.Coprime p a := by
  change Nat.gcd p a = 1
  rcases hp.2 (Nat.gcd p a) (Nat.gcd_dvd_left p a) with h | h
  · exact h
  · have := Nat.gcd_dvd_right p a
    rw [h] at this
    have := Nat.le_of_dvd ha this
    omega

/-- Concatenating digits shifts the prefix by the suffix's length. -/
theorem ofDigits_append_list (pre suffix : List Nat) :
    ofDigits (pre ++ suffix) = ofDigits pre * N ^ suffix.length + ofDigits suffix := by
  induction suffix using snoc_induction with
  | nil => simp [ofDigits]
  | snoc suffix x ih =>
    rw [← List.append_assoc, ofDigits_append, ih, List.length_append, List.length_singleton,
      Nat.pow_succ, ofDigits_append]
    simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.add_assoc]

/-- The value change from replacing digit a by b, after the same prefix and before the same
suffix, is `(b-a) * N^suffix.length` (natural subtraction). -/
theorem digit_change_value (pre suffix : List Nat) (a b : Nat) :
    ofDigits (pre ++ b :: suffix) - ofDigits (pre ++ a :: suffix) =
      (b - a) * N ^ suffix.length := by
  have one (c : Nat) : ofDigits (pre ++ c :: suffix) =
      (N * ofDigits pre + c) * N ^ suffix.length + ofDigits suffix := by
    change ofDigits (pre ++ ([c] ++ suffix)) = _
    rw [← List.append_assoc, ofDigits_append_list, ofDigits_append]
  rw [one b, one a, Nat.add_sub_add_right, ← Nat.mul_sub_right_distrib,
    Nat.add_sub_add_left]

/-- Two different digits at the same position cannot both yield valid AN codewords.
This proves single-digit-error detection and uniqueness of one erased digit. -/
theorem single_change_detected (L : Nat) (pre suffix : List Nat) (a b : Nat)
    (ha : a < N) (hb : b < N) (hne : a ≠ b)
    (hvalid : (layout L).2 ∣ ofDigits (pre ++ a :: suffix)) :
    ¬ (layout L).2 ∣ ofDigits (pre ++ b :: suffix) := by
  have hK := N_lt_K L
  have hcop := (K_prime L).coprime_of_lt (show 0 < N by decide) hK
  have hpow := Nat.Coprime.pow_right suffix.length hcop
  intro hbad
  have not_both (a b : Nat) (ha : a < N) (hb : b < N) (hab : a < b)
      (hva : (layout L).2 ∣ ofDigits (pre ++ a :: suffix))
      (hvb : (layout L).2 ∣ ofDigits (pre ++ b :: suffix)) : False := by
    have hd := Nat.dvd_sub hvb hva
    rw [digit_change_value] at hd
    have hdiv := hpow.dvd_of_dvd_mul_right hd
    have := Nat.le_of_dvd (show 0 < b - a by omega) hdiv
    omega
  by_cases hab : a < b
  · exact not_both a b ha hb hab hvalid hbad
  · exact not_both b a hb ha (by omega) hbad hvalid

/-- With the other digits fixed, at most one possible value for an erased digit is valid. -/
theorem erased_digit_unique (L : Nat) (pre suffix : List Nat) (a b : Nat)
    (ha : a < N) (hb : b < N)
    (hva : (layout L).2 ∣ ofDigits (pre ++ a :: suffix))
    (hvb : (layout L).2 ∣ ofDigits (pre ++ b :: suffix)) : a = b := by
  by_cases e : a = b
  · exact e
  · exact False.elim (single_change_detected L pre suffix a b ha hb e hva hvb)

/-- The numeric effect of swapping adjacent digits (natural subtraction). -/
theorem adjacent_swap_value (pre suffix : List Nat) (a b : Nat) :
    ofDigits (pre ++ b :: a :: suffix) - ofDigits (pre ++ a :: b :: suffix) =
      ((N - 1) * (b - a)) * N ^ suffix.length := by
  have pair (a b : Nat) : ofDigits (pre ++ a :: b :: suffix) =
      (N * (N * ofDigits pre + a) + b) * N ^ suffix.length + ofDigits suffix := by
    change ofDigits (pre ++ ([a, b] ++ suffix)) = _
    rw [← List.append_assoc, ofDigits_append_list]
    have : pre ++ [a, b] = (pre ++ [a]) ++ [b] := by simp
    rw [this, ofDigits_append, ofDigits_append]
  rw [pair b a, pair a b, Nat.add_sub_add_right, ← Nat.mul_sub_right_distrib]
  congr 1
  simp only [N]
  omega

/-- Every swap of unequal adjacent digits is detected, at every position and byte length. -/
theorem adjacent_swap_detected (L : Nat) (pre suffix : List Nat) (a b : Nat)
    (ha : a < N) (hb : b < N) (hne : a ≠ b)
    (hvalid : (layout L).2 ∣ ofDigits (pre ++ a :: b :: suffix)) :
    ¬ (layout L).2 ∣ ofDigits (pre ++ b :: a :: suffix) := by
  have hK := N_lt_K L
  have hcopN := (K_prime L).coprime_of_lt (show 0 < N by decide) hK
  have hpow := Nat.Coprime.pow_right suffix.length hcopN
  have hcop := (K_prime L).coprime_of_lt (show 0 < N - 1 by decide)
    (show N - 1 < (layout L).2 by omega)
  intro hbad
  have not_both (a b : Nat) (ha : a < N) (hb : b < N) (hab : a < b)
      (hva : (layout L).2 ∣ ofDigits (pre ++ a :: b :: suffix))
      (hvb : (layout L).2 ∣ ofDigits (pre ++ b :: a :: suffix)) : False := by
    have hd := Nat.dvd_sub hvb hva
    rw [adjacent_swap_value] at hd
    have hdiv := hcop.dvd_of_dvd_mul_left (hpow.dvd_of_dvd_mul_right hd)
    have := Nat.le_of_dvd (show 0 < b - a by omega) hdiv
    omega
  by_cases hab : a < b
  · exact not_both a b ha hb hab hvalid hbad
  · exact not_both b a hb ha (by omega) hbad hvalid

/-- The numeric effect of swapping digits with one unchanged digit between them. -/
theorem two_apart_swap_value (pre suffix : List Nat) (a b middle : Nat) :
    ofDigits (pre ++ b :: middle :: a :: suffix) -
      ofDigits (pre ++ a :: middle :: b :: suffix) =
      ((N ^ 2 - 1) * (b - a)) * N ^ suffix.length := by
  have triple (a b : Nat) : ofDigits (pre ++ a :: middle :: b :: suffix) =
      (N * (N * (N * ofDigits pre + a) + middle) + b) * N ^ suffix.length +
        ofDigits suffix := by
    change ofDigits (pre ++ ([a, middle, b] ++ suffix)) = _
    rw [← List.append_assoc, ofDigits_append_list]
    have : pre ++ [a, middle, b] = ((pre ++ [a]) ++ [middle]) ++ [b] := by simp
    rw [this, ofDigits_append, ofDigits_append, ofDigits_append]
  rw [triple b a, triple a b, Nat.add_sub_add_right, ← Nat.mul_sub_right_distrib]
  congr 1
  simp only [N]
  omega

/-- K is coprime to N²-1: its factors are N-1 and N+1, both smaller than K. -/
theorem K_coprime_N_squared_sub_one (L : Nat) : Nat.Coprime (layout L).2 (N ^ 2 - 1) := by
  have hK := N_lt_K L
  have hneq : (layout L).2 ≠ N + 1 := by
    intro e
    have h := (isPrime_iff _).mpr (K_prime L)
    rw [e, show isPrime (N + 1) = false by decide +kernel] at h
    cases h
  have hminus := (K_prime L).coprime_of_lt (show 0 < N - 1 by decide)
    (show N - 1 < (layout L).2 by omega)
  have hplus := (K_prime L).coprime_of_lt (show 0 < N + 1 by decide)
    (show N + 1 < (layout L).2 by omega)
  rw [show N ^ 2 - 1 = (N - 1) * (N + 1) by decide +kernel]
  exact hminus.mul_right hplus

/-- Every swap of unequal digits two positions apart is detected. -/
theorem two_apart_swap_detected (L : Nat) (pre suffix : List Nat) (a b middle : Nat)
    (ha : a < N) (hb : b < N) (hne : a ≠ b)
    (hvalid : (layout L).2 ∣ ofDigits (pre ++ a :: middle :: b :: suffix)) :
    ¬ (layout L).2 ∣ ofDigits (pre ++ b :: middle :: a :: suffix) := by
  have hK := N_lt_K L
  have hcopN := (K_prime L).coprime_of_lt (show 0 < N by decide) hK
  have hpow := Nat.Coprime.pow_right suffix.length hcopN
  have hcop := K_coprime_N_squared_sub_one L
  intro hbad
  have not_both (a b : Nat) (ha : a < N) (hb : b < N) (hab : a < b)
      (hva : (layout L).2 ∣ ofDigits (pre ++ a :: middle :: b :: suffix))
      (hvb : (layout L).2 ∣ ofDigits (pre ++ b :: middle :: a :: suffix)) : False := by
    have hd := Nat.dvd_sub hvb hva
    rw [two_apart_swap_value] at hd
    have hdiv := hcop.dvd_of_dvd_mul_left (hpow.dvd_of_dvd_mul_right hd)
    have := Nat.le_of_dvd (show 0 < b - a by omega) hdiv
    omega
  by_cases hab : a < b
  · exact not_both a b ha hb hab hvalid hbad
  · exact not_both b a hb ha (by omega) hbad hvalid

/-! ## Connecting divisibility to the decoder -/

/-- Accepted alphabet digits necessarily form a multiple of K. -/
theorem decode_success_divisible (L : Nat) (ds : List Nat) (data : List UInt8)
    (hlen : ds.length = (layout L).1) (hdigits : ∀ x ∈ ds, x < N)
    (h : decode (ds.map (fun x => alphabet[x]!)) L = .ok data) :
    (layout L).2 ∣ ofDigits ds := by
  rw [decode_alphabet_digits L ds hlen hdigits] at h
  split at h
  · cases h
  · split at h
    · cases h
    · exact Nat.dvd_of_mod_eq_zero (by omega)

/-- A nonmultiple of K is rejected by the decoder, with range taking precedence over check. -/
theorem decode_nonmultiple (L : Nat) (ds : List Nat)
    (hlen : ds.length = (layout L).1) (hdigits : ∀ x ∈ ds, x < N)
    (hbad : ¬ (layout L).2 ∣ ofDigits ds) :
    ∃ e, decode (ds.map (fun x => alphabet[x]!)) L = .error e := by
  rw [decode_alphabet_digits L ds hlen hdigits]
  by_cases hrange : (layout L).2 * 2 ^ (8 * L) ≤ ofDigits ds
  · exact ⟨.range, by simp [hrange]⟩
  · have hrem : ofDigits ds % (layout L).2 ≠ 0 := fun h => hbad (Nat.dvd_of_mod_eq_zero h)
    exact ⟨.check, by simp [hrange, hrem]⟩

/-- Replacing one canonical alphabet digit of a successfully decoded sigil by a different
alphabet digit makes the actual Lean decoder return an error. -/
theorem single_change_decode_rejected (L : Nat) (pre suffix : List Nat) (a b : Nat)
    (data : List UInt8) (ha : a < N) (hb : b < N) (hne : a ≠ b)
    (hlen : (pre ++ a :: suffix).length = (layout L).1)
    (hrest : ∀ x ∈ pre ++ suffix, x < N)
    (hvalid : decode ((pre ++ a :: suffix).map (fun x => alphabet[x]!)) L = .ok data) :
    ∃ e, decode ((pre ++ b :: suffix).map (fun x => alphabet[x]!)) L = .error e := by
  have hchars (c : Nat) (hc : c < N) : ∀ x ∈ pre ++ c :: suffix, x < N := by
    intro x hx
    simp only [List.mem_append, List.mem_cons] at hx
    rcases hx with h | h | h
    · exact hrest x (List.mem_append_left _ h)
    · subst x; exact hc
    · exact hrest x (List.mem_append_right _ h)
  have hv := decode_success_divisible L _ data hlen (hchars a ha) hvalid
  exact decode_nonmultiple L _ (by simpa using hlen) (hchars b hb)
    (single_change_detected L pre suffix a b ha hb hne hv)

end Sigil
