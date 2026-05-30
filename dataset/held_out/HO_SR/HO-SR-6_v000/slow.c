#include <stdint.h>

// SLOW (inverted framing): the canonical Kyber / ML-KEM message bit
// decode loop.  For each ciphertext message byte, expand the 8 bits
// into 8 polynomial coefficients of either 0 or 1665 (= (q+1)/2 for
// q = 3329), in constant time via the bit-mask:
//     mask = -(int16_t)((msg[i] >> j) & 1);    // 0x0000 or 0xFFFF
//     r[8*i + j] = mask & 1665;
// At -O1 (and higher) LLVM trunk and recent GCC recognize the
// `mask & 1665` pattern as "(bit ? 1665 : 0)" and rewrite it into
// `bt msg, j ; jae .Lzero ; mov 1665, r[8i+j]` -- a branch + cmov.
// The branch makes the per-bit timing depend on the secret message
// bit, leaking key bits during ML-KEM decapsulation.  This is the
// vector that powers the Clangover attack (PQShield, 2024).
//
// References:
// - Schneider et al. "When Compilers Break Constant-Time"
//   arXiv:2410.13489 (2024), Example 3
// - LLVM RFC __builtin_ct_select (Trail of Bits, 2024)
// - PQShield "Clangover: a key-recovery attack on Kyber via
//   compiler-induced timing leakage" (2024)
void slow_ho_sr6_v000(const uint8_t *msg, int16_t *r, int n_bytes) {
    for (int i = 0; i < n_bytes; i++) {
        for (int j = 0; j < 8; j++) {
            int16_t mask = -(int16_t)((msg[i] >> j) & 1);
            r[8 * i + j] = mask & 1665;
        }
    }
}
