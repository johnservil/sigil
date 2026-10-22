import Sigil.Spec

/-! # Kernel-checked known answers

These literals pin the format separately from its round-trip theorem. The first example is
hand-calculable: 0 * 7129 = 0, written as two zero digits (U+0030). The other encodings were
proposed by the Python reference; the kernel checks them against the Lean specification.
`Tests.lean` additionally runs the full shared vector corpus using compiled evaluation.
-/

set_option maxRecDepth 100000
set_option maxHeartbeats 10000000
namespace Sigil.KnownAnswers

deriving instance DecidableEq for Except

theorem zero :
    Sigil.encode ([0] : List UInt8) =
    ([48, 48] : List Nat) := by decide +kernel

theorem maximum_byte :
    Sigil.encode ([255] : List UInt8) =
    ([11732, 5350] : List Nat) := by decide +kernel

theorem leading_zero :
    Sigil.encode ([0, 1] : List UInt8) =
    ([48, 116, 6367] : List Nat) := by decide +kernel

theorem sequence_32 :
    Sigil.encode ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] : List UInt8) =
    ([48, 117, 1078, 111, 4942, 5489, 392, 5364, 4836, 4952, 5241, 4890, 671, 5421, 4706, 11715, 5565, 5506, 5596, 5582, 1279, 11740, 4922, 679, 5751, 5394] : List Nat) := by decide +kernel

theorem decode_zero :
    Sigil.decode [48, 48] 1 =
    .ok [0] := by decide +kernel

theorem uppercase_and_ignored :
    Sigil.decode [8203, 32, 65, 5260, 10] 1 =
    .ok [2] := by decide +kernel

theorem length_error :
    Sigil.decode [] 1 =
    .error (.length 0 2) := by decide +kernel

theorem character_error :
    Sigil.decode [8203, 95, 48] 1 =
    .error (.character 2 95) := by decide +kernel

theorem range_error :
    Sigil.decode [11742, 11742] 1 =
    .error (.range) := by decide +kernel

theorem check_error :
    Sigil.decode [48, 49] 1 =
    .error (.check) := by decide +kernel

end Sigil.KnownAnswers
