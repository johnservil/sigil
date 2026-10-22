// Experimental C-ABI arithmetic primitive. Inputs are word, multiplier,
// carry in X0/X1/X2. For inputs below 2^32 the uint64_t result is exact.
// Probe.lean proves the instruction bytes and the complete modeled state change.
.text
.p2align 2
.global sigil_muladd_word
.type sigil_muladd_word, %function
sigil_muladd_word:
    madd x0, x0, x1, x2
    ret
.size sigil_muladd_word, .-sigil_muladd_word
.section .note.GNU-stack,"",%progbits
