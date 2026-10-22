import Sigil.Spec

/-! # Decoding inverts encoding

`decode_encode`: for any data `d`, `decode (encode d) d.length = .ok d`. The
sections below build it from the specification's parts: the alphabet's characters are distinct
and never ignored; the layout's `K` exceeds `N` and fits the room; bytes and digits
convert back and forth. Every proof is checked by Lean's kernel, with no `native_decide`, and
`decode_encode` rests on Lean's three standard axioms alone (`propext`, `Classical.choice`,
`Quot.sound`). -/

namespace Sigil

/-! ## The alphabet -/

/-- Whether a list ascends strictly. -/
def ascending : List Nat → Bool
  | a :: b :: r => a < b && ascending (b :: r)
  | _ => true

theorem alphabet_ascending : ascending alphabet.toList = true := by decide +kernel

theorem alphabet_size : alphabet.size = N := by decide +kernel

theorem alphabet_not_ignored : alphabet.toList.all (fun p => !ignored p) = true := by
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

theorem Array.idxOf?_eq_toList (xs : Array Nat) (a : Nat) : xs.idxOf? a = xs.toList.idxOf? a := by
  cases xs; simp

theorem digit?_alphabet (k : Nat) (hk : k < N) : digit? alphabet[k]! = some k := by
  have hs : k < alphabet.size := by rw [alphabet_size]; exact hk
  have := idxOf?_of_pairwise (pairwise_of_ascending _ alphabet_ascending) k (by simpa using hs)
  rw [getElem!_pos alphabet k hs]
  simp only [digit?, Array.idxOf?_eq_toList, ← Array.getElem_toList, this]
  rfl

theorem ignored_alphabet (k : Nat) (hk : k < N) : ignored alphabet[k]! = false := by
  have hs : k < alphabet.size := by rw [alphabet_size]; exact hk
  rw [getElem!_pos alphabet k hs]
  have := List.all_eq_true.mp alphabet_not_ignored alphabet[k] (by simp)
  simpa using this

/-! ## The layout -/

theorem primeAtMost_le : ∀ r, primeAtMost r ≤ r
  | 0 => Nat.le_refl 0
  | r + 1 => by
    unfold primeAtMost
    split
    · exact Nat.le_refl _
    · have := primeAtMost_le r; omega

theorem le_primeAtMost (p : Nat) (hp : isPrime p = true) : ∀ r, p ≤ r → p ≤ primeAtMost r
  | 0, h => by
    have : p = 0 := by omega
    subst this; simp [isPrime] at hp
  | r + 1, h => by
    unfold primeAtMost
    split
    · exact h
    · rename_i hr
      have : p ≠ r + 1 := fun e => hr (e ▸ hp)
      exact le_primeAtMost p hp r (by omega)

theorem isPrime_1361 : isPrime 1361 = true := by decide +kernel

theorem firstFrom_spec (L : Nat) : ∀ fuel n₀,
    N < primeAtMost (room L (firstFrom L fuel n₀)) ∨ firstFrom L fuel n₀ = n₀ + fuel
  | 0, _ => Or.inr rfl
  | fuel + 1, n => by
    unfold firstFrom
    split
    · exact Or.inl ‹_›
    · rcases firstFrom_spec L fuel (n + 1) with h | h
      · exact Or.inl h
      · right; omega

theorem two_pow_le_N_pow (k : Nat) : 2 ^ k ≤ N ^ k := Nat.pow_le_pow_left (by decide) k

theorem room_last (L : Nat) : 1361 ≤ room L (8 * L + 2) := by
  unfold room
  rw [Nat.le_div_iff_mul_le (Nat.two_pow_pos _), Nat.pow_add]
  have := two_pow_le_N_pow (8 * L)
  have h2 : 1361 ≤ N ^ 2 := by decide
  calc 1361 * 2 ^ (8 * L) ≤ N ^ 2 * N ^ (8 * L) := Nat.mul_le_mul h2 this
    _ = N ^ (8 * L) * N ^ 2 := Nat.mul_comm _ _

/-- The layout's `K` is larger than `N`. -/
theorem N_lt_K (L : Nat) : N < (layout L).2 := by
  simp only [layout]
  rcases firstFrom_spec L (8 * L + 2) 0 with h | h
  · exact h
  · rw [h, Nat.zero_add]
    have := le_primeAtMost 1361 isPrime_1361 _ (room_last L)
    have : N < 1361 := by decide
    omega

/-- The data times `K` fits in the sigil's `n` characters. -/
theorem K_fits (L : Nat) : (layout L).2 * 2 ^ (8 * L) ≤ N ^ (layout L).1 := by
  simp only [layout]
  have := primeAtMost_le (room L (firstFrom L (8 * L + 2) 0))
  unfold room at this
  exact (Nat.le_div_iff_mul_le (Nat.two_pow_pos _)).mp this

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

/-! ## Decoding inverts encoding -/

theorem mapM_ok {α β ε : Type} (F : α → Except ε β) (g : α → β) :
    ∀ l : List α, (∀ a ∈ l, F a = .ok (g a)) → l.mapM F = .ok (l.map g)
  | [], _ => rfl
  | a :: l, h => by
    rw [List.mapM_cons, h a (List.mem_cons_self ..),
      mapM_ok F g l (fun x hx => h x (List.mem_cons_of_mem _ hx))]
    rfl

/-- On alphabet digits of the specified length, decoding is exactly the AN code's range and
remainder checks, followed by conversion of the quotient to bytes. -/
theorem decode_alphabet_digits (L : Nat) (ds : List Nat)
    (hlen : ds.length = (layout L).1) (hdigits : ∀ x ∈ ds, x < N) :
    decode (ds.map (fun x => alphabet[x]!)) L =
      if (layout L).2 * 2 ^ (8 * L) ≤ ofDigits ds then .error .range
      else if ofDigits ds % (layout L).2 ≠ 0 then .error .check
      else .ok (toBytes (ofDigits ds / (layout L).2) L) := by
  simp only [decode]
  generalize hs : ds.map (fun x => alphabet[x]!) = s
  have hchar : ∀ a ∈ s.zipIdx 1, ∃ x, x ∈ ds ∧ a.1 = alphabet[x]! := by
    intro a ha
    have := List.fst_mem_of_mem_zipIdx ha
    rw [← hs, List.mem_map] at this
    obtain ⟨x, hx, e⟩ := this
    exact ⟨x, hx, e.symm⟩
  have hfilter : (s.zipIdx 1).filter (fun x => !ignored x.fst) = s.zipIdx 1 := by
    rw [List.filter_eq_self]
    intro a ha
    obtain ⟨x, hx, e⟩ := hchar a ha
    rw [e, ignored_alphabet x (hdigits x hx)]
    rfl
  have hslen : (s.zipIdx 1).length = (layout L).1 := by
    rw [List.length_zipIdx, ← hs, List.length_map, hlen]
  have hds : (s.zipIdx 1).map (fun a => (digit? a.1).getD 0) = ds := by
    rw [show (fun a : Nat × Nat => (digit? a.1).getD 0) = (fun p => (digit? p).getD 0) ∘ Prod.fst
      from rfl, ← List.map_map, List.zipIdx_map_fst, ← hs, List.map_map]
    conv => rhs; rw [← List.map_id ds]
    apply List.map_congr_left
    intro x hx
    simp [digit?_alphabet x (hdigits x hx)]
  simp only [hfilter, hslen, ne_eq, not_true_eq_false, if_false]
  rw [mapM_ok _ (fun a => (digit? a.1).getD 0) _ ?chars]
  case chars =>
    intro a ha
    obtain ⟨x, hx, e⟩ := hchar a ha
    simp only [e, digit?_alphabet x (hdigits x hx)]
    rfl
  simp only [bind, Except.bind, pure, Except.pure]
  rw [hds]
  simp only [throw, throwThe]
  split <;> simp_all <;> rfl

/-- Decoding `d`'s sigil, told `d`'s length, gives back `d`. -/
theorem decode_encode (d : List UInt8) : decode (encode d) d.length = .ok d := by
  have hK := N_lt_K d.length
  have hfit := K_fits d.length
  have hlt := ofBytes_lt d
  have hprod : ofBytes d * (layout d.length).2 < (layout d.length).2 * 2 ^ (8 * d.length) := by
    rw [Nat.mul_comm (layout d.length).2]
    exact Nat.mul_lt_mul_of_pos_right hlt (by omega)
  have hw : ofBytes d * (layout d.length).2 < N ^ (layout d.length).1 := by omega
  unfold encode
  rw [decode_alphabet_digits _ _ (toDigits_length _ _) (toDigits_lt _ _),
    ofDigits_toDigits, Nat.mod_eq_of_lt hw]
  simp [Nat.not_le_of_lt hprod, Nat.mul_mod_left,
    Nat.mul_div_cancel _ (show 0 < (layout d.length).2 by omega), toBytes_ofBytes]

end Sigil
