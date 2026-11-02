import Sigil.Spec

/-! # Kernel-checked known answers

These literals pin the format separately from its round-trip theorem: the Python reference
proposed them, and the kernel checks them against the Lean specification. `Tests.lean` also runs
the full shared vector corpus using compiled evaluation.
-/

set_option maxRecDepth 100000
set_option maxHeartbeats 10000000
namespace Sigil.KnownAnswers

deriving instance DecidableEq for Except

theorem zero :
    Sigil.encode ([0] : List UInt8) =
    ([2339, 43524] : List Nat) := by decide +kernel

theorem maximum_byte :
    Sigil.encode ([255] : List UInt8) =
    ([43172, 5542] : List Nat) := by decide +kernel

theorem leading_zero :
    Sigil.encode ([0, 1] : List UInt8) =
    ([2310, 2321, 5691] : List Nat) := by decide +kernel

theorem sequence_32 :
    Sigil.encode ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] : List UInt8) =
    ([2308, 2430, 5434, 43159, 5366, 43177, 6360, 3501, 42457, 43166, 42358, 5817, 4855, 42256, 11736, 2832, 42302, 5310, 4848, 5627, 5813, 42346, 3116, 42437, 3096] : List Nat) := by decide +kernel

theorem decode_zero :
    Sigil.decode [2339, 43524] 1 =
    .ok [0] := by decide +kernel

theorem skipped_characters :
    Sigil.decode [8203, 32, 2343, 8288, 43186, 10] 1 =
    .ok [2] := by decide +kernel

theorem length_error :
    Sigil.decode [] 1 =
    .error (.length 0 2) := by decide +kernel

theorem character_error :
    Sigil.decode [8203, 8238, 43524] 1 =
    .error (.character 2 8238) := by decide +kernel

theorem check_error :
    Sigil.decode [2339, 43525] 1 =
    .error (.check) := by decide +kernel

theorem range_error :
    Sigil.decode [43594, 5438] 1 =
    .error (.range) := by decide +kernel

theorem marker_error :
    Sigil.decode [2438, 43138] 1 =
    .error (.marker) := by decide +kernel

end Sigil.KnownAnswers
