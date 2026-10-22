// Integration smoke test. The caller, loader and startup code are tested here,
// outside Probe.lean's proof boundary.
#include "muladd.h"
#include <inttypes.h>
#include <stdio.h>

int main(void) {
    uint64_t result = sigil_muladd_word(UINT32_MAX, UINT32_MAX, UINT32_MAX);
    printf("%" PRIu64 "\n", result);
    return result == UINT64_C(0xffffffff00000000) ? 0 : 1;
}
