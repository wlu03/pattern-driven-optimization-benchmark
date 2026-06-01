#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// FAST: 6-bit registers densely packed into a 12 KB byte buffer.  Each
// register spans 6 bits; consecutive registers cross byte boundaries.
// We use the Redis HLL_DENSE_GET_REGISTER style cross-byte read:
//     bit  = idx * 6;
//     byte = bit >> 3;       // byte index
//     fb   = bit & 7;        // fractional bit offset
//     val  = ((regs[byte] >> fb) | (regs[byte+1] << (8 - fb))) & 0x3F
//
// 16384 registers * 6 bits = 12288 bytes (12 KB) -- 25% less memory
// than the 16 KB naive layout.  In a cardinality-monitoring workload
// that does many estimator passes, the smaller working set fits more
// comfortably in L1 / L2.
//
// Cite: Redis HLL_DENSE_GET_REGISTER / HLL_DENSE_SET_REGISTER macros
// (antirez 2014, src/hyperloglog.c).
#define HO_DS6_N_REG   16384

static inline uint8_t fast_get(const uint8_t *regs, uint32_t idx) {
    uint32_t bit  = idx * 6;
    uint32_t byte = bit >> 3;
    uint32_t fb   = bit & 7;
    uint8_t b0 = regs[byte];
    uint8_t b1 = regs[byte + 1];
    return (uint8_t)(((b0 >> fb) | (b1 << (8 - fb))) & 0x3F);
}

static inline void fast_set(uint8_t *regs, uint32_t idx, uint8_t val) {
    uint32_t bit  = idx * 6;
    uint32_t byte = bit >> 3;
    uint32_t fb   = bit & 7;
    uint16_t w = (uint16_t)regs[byte] | ((uint16_t)regs[byte + 1] << 8);
    uint16_t mask = (uint16_t)(0x3Fu << fb);
    w = (uint16_t)((w & ~mask) | ((uint16_t)(val & 0x3F) << fb));
    regs[byte]     = (uint8_t)(w & 0xFF);
    regs[byte + 1] = (uint8_t)(w >> 8);
}

// End-to-end: populate then estimator-poll, same shape as slow_ho_ds6_v002.
double fast_ho_ds6_v002(const uint8_t *vals, uint8_t *regs_buf, int n_polls,
                          int *zeros_out) {
    // Zero the buffer first since we OR into it during set.
    memset(regs_buf, 0, HO_DS6_N_REG * 6 / 8 + 1);
    for (uint32_t i = 0; i < HO_DS6_N_REG; i++) {
        fast_set(regs_buf, i, vals[i]);
    }
    double sum = 0.0;
    int zeros = 0;
    for (int p = 0; p < n_polls; p++) {
        sum = 0.0; zeros = 0;
        for (uint32_t i = 0; i < HO_DS6_N_REG; i++) {
            uint8_t r = fast_get(regs_buf, i);
            sum += 1.0 / (double)(1ULL << r);
            if (r == 0) zeros++;
        }
    }
    *zeros_out = zeros;
    return sum;
}
