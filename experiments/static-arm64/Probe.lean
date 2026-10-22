import Arm.Exec

/-! Static feasibility probe against LNSym's AArch64 model. The byte literals are checked
against the freshly linked library by check.py. This covers one arithmetic primitive, including
its return and exact final state; it does not establish correctness of Sigil or its loader. -/

open BitVec
namespace SigilStatic

/-- Little-endian bytes of `madd x0, x0, x1, x2; ret`. -/
def codeBytes : List Nat := [0x00, 0x08, 0x01, 0x9b, 0xc0, 0x03, 0x5f, 0xd6]

/-- Decode a four-byte little-endian instruction word from the literal bytes. -/
def wordAt (i : Nat) : BitVec 32 := BitVec.ofNat 32
  (codeBytes[i]! + 256 * codeBytes[i + 1]! + 65536 * codeBytes[i + 2]! +
    16777216 * codeBytes[i + 3]!)

theorem word0 : wordAt 0 = 0x9b010800#32 := by decide
theorem word4 : wordAt 4 = 0xd65f03c0#32 := by decide

def maddInst : ArmInst := .DPR (.Data_processing_three_source
  { sf := 1#1, op54 := 0#2, op31 := 0#3, Rm := 1#5, o0 := 0#1,
    Ra := 2#5, Rn := 0#5, Rd := 0#5 })
def retInst : ArmInst := .BR (.Uncond_branch_reg
  { opc := 2#4, op2 := 31#5, op3 := 0#6, Rn := 30#5, op4 := 0#5 })

theorem decode_madd : decode_raw_inst 0x9b010800#32 = some maddInst := by decide
theorem decode_ret : decode_raw_inst 0xd65f03c0#32 = some retInst := by decide

/-- The model's instruction map, built from the byte literals at any load address. -/
def code (pc : BitVec 64) : Program := [(pc, wordAt 0), (pc + 4#64, wordAt 4)]

theorem madd_step (s : ArmState) (pc : BitVec 64)
    (hp : read_pc s = pc) (hc : s.program = code pc) (he : read_err s = .None) :
    stepi s = write_pc (pc + 4#64)
      (write_gpr 64 0#5 (read_gpr 64 2#5 s + read_gpr 64 0#5 s * read_gpr 64 1#5 s) s) := by
  have hf : fetch_inst pc s = some 0x9b010800#32 := by
    unfold fetch_inst
    rw [hc]
    simp [code, word0, word4, Map.find?]
  rw [stepi_eq_of_fetch_inst_of_decode_raw_inst s pc _ maddInst he hp hf decode_madd]
  change write_pc (read_pc (write_gpr 64 0#5
      (read_gpr 64 2#5 s + read_gpr 64 0#5 s * read_gpr 64 1#5 s) s) + 4#64)
    (write_gpr 64 0#5 (read_gpr 64 2#5 s + read_gpr 64 0#5 s * read_gpr 64 1#5 s) s) = _
  simp only [read_pc, write_gpr, r_of_w_different (by decide : StateField.PC ≠ .GPR 0#5)]
  change write_pc (read_pc s + 4#64) _ = _
  rw [hp]

theorem ret_step (s : ArmState) (pc : BitVec 64)
    (hp : read_pc s = pc + 4#64) (hc : s.program = code pc) (he : read_err s = .None) :
    stepi s = write_pc (read_gpr 64 30#5 s) s := by
  have hne : pc ≠ pc + 4#64 := by
    intro h
    have hn := congrArg BitVec.toNat h
    simp only [BitVec.toNat_add, BitVec.toNat_ofNat] at hn
    omega
  have hf : fetch_inst (pc + 4#64) s = some 0xd65f03c0#32 := by
    unfold fetch_inst
    rw [hc]
    simp [code, word0, word4, Map.find?, hne]
  rw [stepi_eq_of_fetch_inst_of_decode_raw_inst s (pc + 4#64) _ retInst he hp hf decode_ret]
  rfl

/-- For every initial register and memory state and every load address, these instruction
words return the modular multiply-add in X0 and preserve all state except X0 and PC. -/
theorem muladd_word_state (s : ArmState) (pc : BitVec 64)
    (hp : read_pc s = pc) (hc : s.program = code pc) (he : read_err s = .None) :
    run 2 s = write_pc (read_gpr 64 30#5 s)
      (write_gpr 64 0#5 (read_gpr 64 2#5 s + read_gpr 64 0#5 s * read_gpr 64 1#5 s) s) := by
  change stepi (stepi s) = _
  rw [madd_step s pc hp hc he]
  rw [ret_step _ pc]
  · simp only [read_gpr, write_pc, write_gpr, state_simp_rules,
      r_of_w_different (by decide : StateField.GPR 30#5 ≠ .PC),
      r_of_w_different (by decide : StateField.GPR 30#5 ≠ .GPR 0#5)]
  · simp only [read_pc, write_pc, state_simp_rules]
  · simp only [write_pc, write_gpr, w_program, hc]
  · simp only [read_err, write_pc, write_gpr,
      r_of_w_different (by decide : StateField.ERR ≠ .PC),
      r_of_w_different (by decide : StateField.ERR ≠ .GPR 0#5)]
    exact he

/-- On 32-bit inputs, multiply-add does not wrap: the returned natural number is exact. -/
theorem muladd_word_exact (s : ArmState) (pc : BitVec 64)
    (hp : read_pc s = pc) (hc : s.program = code pc) (he : read_err s = .None)
    (hw : (read_gpr 64 0#5 s).toNat < 2 ^ 32)
    (hm : (read_gpr 64 1#5 s).toNat < 2 ^ 32)
    (hcarry : (read_gpr 64 2#5 s).toNat < 2 ^ 32) :
    (read_gpr 64 0#5 (run 2 s)).toNat =
      (read_gpr 64 0#5 s).toNat * (read_gpr 64 1#5 s).toNat +
        (read_gpr 64 2#5 s).toNat := by
  have hout : read_gpr 64 0#5 (run 2 s) =
      read_gpr 64 2#5 s + read_gpr 64 0#5 s * read_gpr 64 1#5 s := by
    rw [muladd_word_state s pc hp hc he]
    simp only [read_gpr, write_pc, write_gpr,
      r_of_w_different (by decide : StateField.GPR 0#5 ≠ .PC), r_of_w_same,
      BitVec.setWidth_eq]
  rw [hout, BitVec.toNat_add, BitVec.toNat_mul]
  have hprod : (read_gpr 64 0#5 s).toNat * (read_gpr 64 1#5 s).toNat ≤
      (2 ^ 32 - 1) * (2 ^ 32 - 1) := Nat.mul_le_mul (by omega) (by omega)
  rw [Nat.mod_eq_of_lt (by omega), Nat.mod_eq_of_lt (by omega)]
  omega

#print axioms muladd_word_state
#print axioms muladd_word_exact
end SigilStatic
