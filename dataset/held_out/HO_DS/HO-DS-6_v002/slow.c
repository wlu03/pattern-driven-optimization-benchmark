#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// SLOW: naive HLL register layout -- one 6-bit value per byte
// (uint8_t regs[16384] = 16 KB).  Each register fits comfortably in a
// byte but wastes the top 2 bits of every byte.  Total memory: 16 KB
// (33% larger than the 12 KB densely-packed layout).  The hot
// estimator pass touches all 16 KB on every cardinality poll.
//
// Reference baseline for the Redis HLL_DENSE_GET_REGISTER cross-byte
// 6-bit packing that fast.c uses.
#define HO_DS6_N_REG  16384

static inline void slow_set(uint8_t *regs, uint32_t idx, uint8_t val) {
    regs[idx] = val & 0x3F;
}

static inline uint8_t slow_get(const uint8_t *regs, uint32_t idx) {
    return regs[idx] & 0x3F;
}

// End-to-end: populate every register with `vals[i]`, then run
// `n_polls` estimator passes.  Returns the harmonic-mean estimator sum
// from the last poll (a deterministic function of the populated values
// that both slow and fast must agree on).
double slow_ho_ds6_v002(const uint8_t *vals, uint8_t *regs_buf, int n_polls,
                          int *zeros_out) {
    // Populate.
    for (uint32_t i = 0; i < HO_DS6_N_REG; i++) {
        slow_set(regs_buf, i, vals[i]);
    }
    // Polls.
    double sum = 0.0;
    int zeros = 0;
    for (int p = 0; p < n_polls; p++) {
        sum = 0.0; zeros = 0;
        for (uint32_t i = 0; i < HO_DS6_N_REG; i++) {
            uint8_t r = slow_get(regs_buf, i);
            sum += 1.0 / (double)(1ULL << r);
            if (r == 0) zeros++;
        }
    }
    *zeros_out = zeros;
    return sum;
}
