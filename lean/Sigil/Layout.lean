import Sigil.Theorems

/-! # The layout's mathematical contract

The trial-division predicate agrees with primality: a number at least two whose only natural
number divisors are one and itself. The search chooses the largest such prime fitting the room,
and the smallest character count whose room can hold a prime above the alphabet size.
-/

namespace Sigil

/-- A prime is at least two and has only one and itself as natural-number divisors. -/
def Prime (k : Nat) : Prop := 2 ≤ k ∧ ∀ d : Nat, d ∣ k → d = 1 ∨ d = k

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

/-- The downward search either finds a mathematical prime or returns zero. -/
theorem primeAtMost_zero_or_prime : ∀ r, primeAtMost r = 0 ∨ Prime (primeAtMost r)
  | 0 => Or.inl rfl
  | r + 1 => by
    unfold primeAtMost
    split
    · exact Or.inr ((isPrime_iff _).mp ‹_›)
    · exact primeAtMost_zero_or_prime r

/-- The layout's K is mathematically prime, not merely accepted by its test. -/
theorem K_prime (L : Nat) : Prime (layout L).2 := by
  have hK := N_lt_K L
  rcases primeAtMost_zero_or_prime (room L (layout L).1) with h | h
  · change (layout L).2 = 0 at h
    omega
  · exact h

/-- Every mathematical prime fitting the selected character count is at most K. -/
theorem K_largest (L p : Nat) (hp : Prime p)
    (hfit : p * 2 ^ (8 * L) ≤ N ^ (layout L).1) : p ≤ (layout L).2 := by
  apply le_primeAtMost p ((isPrime_iff p).mpr hp)
  exact (Nat.le_div_iff_mul_le (Nat.two_pow_pos _)).mpr hfit

/-- The upward search has rejected every earlier candidate, including when its fuel runs out. -/
theorem firstFrom_minimal (L : Nat) : ∀ fuel n₀ m,
    n₀ ≤ m → m < firstFrom L fuel n₀ → primeAtMost (room L m) ≤ N
  | 0, _, _, hlo, hhi => by simp only [firstFrom] at hhi; omega
  | fuel + 1, n, m, hlo, hhi => by
    unfold firstFrom at hhi
    split at hhi
    · omega
    · rename_i hn
      by_cases e : m = n
      · subst m; omega
      · exact firstFrom_minimal L fuel (n + 1) m (by omega) hhi

/-- Fewer characters cannot hold any prime above N beside L bytes. -/
theorem layout_minimal (L m p : Nat) (hm : m < (layout L).1) (hp : Prime p)
    (hfit : p * 2 ^ (8 * L) ≤ N ^ m) : p ≤ N := by
  have hsmall := firstFrom_minimal L (8 * L + 2) 0 m (Nat.zero_le _) hm
  have hp_le := le_primeAtMost p ((isPrime_iff p).mpr hp) (room L m)
    ((Nat.le_div_iff_mul_le (Nat.two_pow_pos _)).mpr hfit)
  omega

/-- The layout's full mathematical contract: a prime above N, the largest that fits,
using the fewest possible characters. Quantification covers every byte length. -/
theorem layout_contract (L : Nat) :
    let (n, K) := layout L
    Prime K ∧ N < K ∧ K * 2 ^ (8 * L) ≤ N ^ n ∧
    (∀ p, Prime p → p * 2 ^ (8 * L) ≤ N ^ n → p ≤ K) ∧
    (∀ m, m < n → ∀ p, Prime p → p * 2 ^ (8 * L) ≤ N ^ m → p ≤ N) := by
  exact ⟨K_prime L, N_lt_K L, K_fits L, K_largest L,
    fun m hm p hp hfit => layout_minimal L m p hm hp hfit⟩

end Sigil
