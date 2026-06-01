#include <stdint.h>
#include <string.h>

// SLOW (inverted framing): the canonical BearSSL constant-time
// conditional-move via mask.  The intent: copy `len` bytes from src
// to dst IF `x != 0`, in constant time regardless of x's value.  The
// idiom is:
//     mask = -(uint64_t)(((x | -x) >> 31) ^ 1) -- 0 if x!=0, all-1s if x==0
//     for i in [0,len): dst[i] = (dst[i] & mask) | (src[i] & ~mask)
// Both clang and gcc at -O3 recognize the (x | -x) >> 31 pattern as
// "is x zero?" and rewrite the loop into a `test/je/jmp memcpy@PLT`
// sequence -- which is exactly the branch the CT discipline was
// trying to avoid.
//
// References:
// - Pornin "On the Tightness of Constant-Time Cryptographic
//   Constructions" IACR eprint 2025/435, Section 3
// - BearSSL inner.h CT macros
// - LLVM RFC for __builtin_ct_select (Trail of Bits, 2024)
void slow_ho_sr5_v003(uint8_t *dst, const uint8_t *src, int x, int len) {
    // mask = 0 if x != 0 (do copy), all-ones if x == 0 (keep dst)
    uint64_t cond = (uint64_t)(((uint32_t)(x | -x)) >> 31) ^ 1;
    uint64_t mask = -cond;
    for (int i = 0; i < len; i++) {
        dst[i] = (uint8_t)((dst[i] & mask) | (src[i] & ~mask));
    }
}
