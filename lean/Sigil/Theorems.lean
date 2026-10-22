import Sigil.Spec

/-! # Theorems about the specification

BLAKE3's output has the length asked for (`deriveKey_length`), so the check's BLAKE3 output is
the 8 bytes it reads. -/

namespace Sigil

/-! ## BLAKE3's output has the length asked for -/

theorem bytesLE_size (ws : List Blake3.Word) : (Blake3.bytesLE ws).size = 4 * ws.length := by
  simp only [Blake3.bytesLE, ByteArray.size, List.size_toArray, List.length_flatMap,
    List.length_cons, List.length_nil]
  induction ws with
  | nil => simp
  | cons w ws ih => simp [List.sum_cons, ih]; omega

theorem output_size (root : Blake3.Node) (len : Nat) : (Blake3.output root len).size = len := by
  simp only [Blake3.output, ByteArray.size_extract, bytesLE_size, List.length_flatten,
    List.map_map]
  have : ((List.range ((len + 63) / 64)).map
      (List.length ∘ fun i => (Blake3.BLAKE3_COMPRESS root.h root.m i.toUInt64 root.len
        (root.flags ||| Blake3.ROOT)).toList)).sum = 16 * ((len + 63) / 64) := by
    simp only [Function.comp_def, Vector.length_toList]
    generalize (len + 63) / 64 = k
    induction k with
    | zero => simp
    | succ k ih => simp [List.range_succ, List.sum_append, ih]; omega
  rw [this]; omega

theorem deriveKey_length (context : String) (x : List UInt8) (len : Nat) :
    (deriveKey context x len).length = len := by
  unfold deriveKey Blake3.derive_key Blake3.blake3
  rw [Array.length_toList]
  exact output_size _ len

end Sigil
