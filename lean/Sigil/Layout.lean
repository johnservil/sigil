import Sigil.Spec

/-! # The layout's mathematical contract

The trial-division predicate agrees with primality: a number at least two whose only natural
number divisors are one and itself. Every layout's K is such a prime, larger than the alphabet
size, and fits the room beside the marked data; the layout's letter count is the fewest with room
for any prime above the alphabet size.
-/

namespace Sigil

/-- A prime is at least two and has only one and itself as natural-number divisors. -/
def Prime (k : Nat) : Prop := 2 ≤ k ∧ ∀ d : Nat, d ∣ k → d = 1 ∨ d = k

/-- Whether no `p` from `p₀` divides `k`, for `p` up to `√k`, trying at most `fuel` of them. -/
def noDivisorFrom (k : Nat) : (fuel p₀ : Nat) → Bool
  | 0, _ => true
  | fuel + 1, p => k < p * p || (k % p ≠ 0 && noDivisorFrom k fuel (p + 1))

/-- Whether `k` is prime, by trial division. -/
def isPrime (k : Nat) : Bool := 2 ≤ k && noDivisorFrom k k 2

/-- The trial-division loop tests exactly the divisors in its bounded interval up to √k. -/
theorem noDivisorFrom_iff (k : Nat) : ∀ fuel p,
    noDivisorFrom k fuel p = true ↔
      ∀ d, p ≤ d → d < p + fuel → d * d ≤ k → k % d ≠ 0
  | 0, p => by simp [noDivisorFrom]; omega
  | fuel + 1, p => by
    rw [noDivisorFrom]
    simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq]
    rw [noDivisorFrom_iff k fuel (p + 1)]
    constructor
    · intro h d hpd hdf hdk
      rcases h with hstop | ⟨hp, hrest⟩
      · have := Nat.mul_self_le_mul_self hpd; omega
      · by_cases e : d = p
        · subst d; exact hp
        · exact hrest d (by omega) (by omega) hdk
    · intro h
      by_cases hstop : k < p * p
      · exact Or.inl hstop
      · right
        exact ⟨h p (by omega) (by omega) (by omega),
          fun d hpd hdf hdk => h d (by omega) (by omega) hdk⟩

/-- A proper divisor bigger than one gives a divisor no larger than √k. -/
theorem small_divisor {k d : Nat} (hdk : d ∣ k) (hd : 2 ≤ d) (hproper : d < k) :
    ∃ f, 2 ≤ f ∧ f * f ≤ k ∧ f ∣ k := by
  obtain ⟨q, hq⟩ := hdk
  have hq2 : 2 ≤ q := by
    by_cases h : 2 ≤ q
    · exact h
    · have : q = 0 ∨ q = 1 := by omega
      rcases this with h | h <;> simp_all
  by_cases h : d ≤ q
  · refine ⟨d, hd, ?_, ⟨q, hq⟩⟩
    rw [hq]
    exact Nat.mul_le_mul_left d h
  · refine ⟨q, hq2, ?_, ⟨d, ?_⟩⟩
    · rw [hq]; exact Nat.mul_le_mul_right q (by omega)
    · rw [hq, Nat.mul_comm]

/-- The executable primality predicate means exactly mathematical primality. -/
theorem isPrime_iff (k : Nat) : isPrime k = true ↔ Prime k := by
  simp only [isPrime, Bool.and_eq_true, decide_eq_true_eq, noDivisorFrom_iff]
  constructor
  · rintro ⟨hk, htest⟩
    refine ⟨hk, fun d hd => ?_⟩
    by_cases e : d = 1
    · exact Or.inl e
    by_cases e' : d = k
    · exact Or.inr e'
    have hdpos : 0 < d := Nat.pos_of_dvd_of_pos hd (by omega)
    have hdle : d ≤ k := Nat.le_of_dvd (by omega) hd
    obtain ⟨f, hf, hfk, hfd⟩ := small_divisor hd (by omega) (by omega)
    have hfle : f ≤ k := Nat.le_of_dvd (by omega) hfd
    exact False.elim (htest f hf (by omega) hfk (Nat.mod_eq_zero_of_dvd hfd))
  · rintro ⟨hk, hprime⟩
    refine ⟨hk, fun d hd hdf hsq hmod => ?_⟩
    rcases hprime d (Nat.dvd_of_mod_eq_zero hmod) with h | h
    · omega
    · subst d
      have : k * 2 ≤ k * k := Nat.mul_le_mul_left k hk
      omega

/-! ## The layout -/

/-- The room's exponent is 12 to 22 at every length, and with it the letter count. -/
theorem roomBits_range (L : Nat) : 12 ≤ roomBits L ∧ roomBits L ≤ 22 ∧
    11 * letters L = 8 * L + 2 + roomBits L := by
  simp only [roomBits, letters]; omega

set_option maxHeartbeats 10000000 in
/-- Each check prime is prime, larger than `N`, and at most its room. -/
theorem checkPrimes_facts : ∀ i, i < 11 →
    isPrime (checkPrimes.getD i 0) = true ∧ N < checkPrimes.getD i 0 ∧
      checkPrimes.getD i 0 ≤ 2 ^ (i + 12) := by
  decide +kernel

theorem layout_K (L : Nat) : (layout L).2 = checkPrimes.getD (roomBits L - 12) 0 := by
  simp only [layout]

theorem K_prime (L : Nat) : Prime (layout L).2 := by
  have := roomBits_range L
  exact (isPrime_iff _).mp (checkPrimes_facts (roomBits L - 12) (by omega)).1

/-- The layout's `K` is larger than `N`. -/
theorem N_lt_K (L : Nat) : N < (layout L).2 := by
  have := roomBits_range L
  exact (checkPrimes_facts (roomBits L - 12) (by omega)).2.1

theorem N_pow (n : Nat) : N ^ n = 2 ^ (11 * n) := by
  rw [show N = 2 ^ 11 from rfl, ← Nat.pow_mul]

/-- `K` times the marked data's bound fits in the sigil's `n` letters. -/
theorem K_fits (L : Nat) : (layout L).2 * 2 ^ (8 * L + 2) ≤ N ^ (layout L).1 := by
  have hr := roomBits_range L
  have hK := (checkPrimes_facts (roomBits L - 12) (by omega)).2.2
  rw [show roomBits L - 12 + 12 = roomBits L by omega] at hK
  rw [layout_K, N_pow, show (layout L).1 = letters L from rfl, hr.2.2,
    Nat.pow_add 2 (8 * L + 2) (roomBits L), Nat.mul_comm (2 ^ (8 * L + 2)) (2 ^ roomBits L)]
  exact Nat.mul_le_mul_right _ hK

/-- Fewer letters leave no room for any prime above `N` beside the marked data. -/
theorem layout_minimal (L m p : Nat) (hm : m < (layout L).1) (_hp : Prime p)
    (hfit : p * 2 ^ (8 * L + 2) ≤ N ^ m) : p ≤ N := by
  have hr := roomBits_range L
  have hm' : 11 * m + 11 ≤ 8 * L + 2 + 22 := by
    have : m + 1 ≤ letters L := hm
    omega
  rw [N_pow] at hfit
  have : N ^ m ≤ 2 ^ 11 * 2 ^ (8 * L + 2) := by
    rw [N_pow, ← Nat.pow_add]; exact Nat.pow_le_pow_right (by decide) (by omega)
  rw [N_pow] at this
  have h := Nat.le_trans hfit this
  exact Nat.le_of_mul_le_mul_right h (Nat.two_pow_pos _)

/-- The layout's full mathematical contract: a prime above N that fits beside the marked data,
using the fewest possible letters. Quantification covers every byte length. -/
theorem layout_contract (L : Nat) :
    let (n, K) := layout L
    Prime K ∧ N < K ∧ K * 2 ^ (8 * L + 2) ≤ N ^ n ∧
    (∀ m, m < n → ∀ p, Prime p → p * 2 ^ (8 * L + 2) ≤ N ^ m → p ≤ N) :=
  ⟨K_prime L, N_lt_K L, K_fits L, fun m hm p hp hfit => layout_minimal L m p hm hp hfit⟩

end Sigil
