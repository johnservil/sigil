#ifndef SIGIL_STATIC_PROBE_H
#define SIGIL_STATIC_PROBE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Experimental primitive, not a Sigil encoding API.
// Returns (word * multiplier + carry) modulo 2^64 for all inputs;
// when each input is below 2^32, the result is exact. The proof assumes the AArch64
// instruction model and the usual valid code/return-address environment.
uint64_t sigil_muladd_word(uint64_t word, uint64_t multiplier, uint64_t carry);

#ifdef __cplusplus
}
#endif
#endif
