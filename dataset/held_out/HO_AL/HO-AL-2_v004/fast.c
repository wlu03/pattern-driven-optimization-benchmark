#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// FAST: HyperLogLog with m = 16384 = 2^14 6-bit registers (12 KB total).
// For each key we hash, take the low 14 bits as the register index and
// the leading-zeros of the high 50 bits + 1 as the rank.  Update is
// register[idx] = max(register[idx], rank).  Estimate cardinality with
// the standard HLL harmonic-mean formula (alpha_m * m^2 / sum(2^-r)).
//
// O(1) memory (fixed 12 KB regardless of N), O(N) time but ~1 cache
// line per insert vs O(N) heap allocations in the slow path.  Standard
// HLL theoretical error is 1.04/sqrt(m) ~= 0.81% at m=16384, so we
// allow 2% relative error in the harness.
//
// Cite: Redis HyperLogLog source (hyperloglog.c) + antirez 2014 blog
// post "Stream algorithms and HyperLogLog".
#define HO_AL2_P     14
#define HO_AL2_M     (1u << HO_AL2_P)   // 16384 registers
#define HO_AL2_PMASK (HO_AL2_M - 1u)

static inline uint64_t ho_al2_mix(uint64_t k) {
    // MurmurHash3 finalizer.  Strong avalanche; cheap.
    k ^= k >> 33; k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33; k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

long fast_ho_al2_v004(uint64_t *keys, long n) {
    // Use uint8_t per register for simplicity (16 KB vs the strict 12 KB
    // 6-bit packing covered separately by HO-DS-6).  Estimator is
    // identical; only memory differs.
    uint8_t *reg = calloc(HO_AL2_M, 1);
    if (!reg) return 0;

    for (long i = 0; i < n; i++) {
        uint64_t h = ho_al2_mix(keys[i]);
        uint32_t idx = (uint32_t)(h & HO_AL2_PMASK);
        // Rank (Redis convention): position of first 1 in the suffix
        // (high 64-P bits), counting from LSB starting at 1.  Equivalent
        // to __builtin_ctzll on (suffix | sentinel-at-bit-Q) + 1.
        uint64_t suffix = (h >> HO_AL2_P) | (1ULL << (64 - HO_AL2_P));
        int rank = __builtin_ctzll(suffix) + 1;
        if ((uint8_t)rank > reg[idx]) reg[idx] = (uint8_t)rank;
    }

    // Harmonic-mean estimate, with the alpha_m constant for m=16384.
    double sum = 0.0;
    int zeros = 0;
    for (uint32_t i = 0; i < HO_AL2_M; i++) {
        sum += 1.0 / (double)(1ULL << reg[i]);
        if (reg[i] == 0) zeros++;
    }
    const double alpha = 0.7213 / (1.0 + 1.079 / (double)HO_AL2_M);
    double m = (double)HO_AL2_M;
    double est = alpha * m * m / sum;

    // Small-range correction (linear counting) when many registers are 0.
    if (est <= 2.5 * m && zeros > 0) {
        est = m * log(m / (double)zeros);
    }
    free(reg);
    return (long)(est + 0.5);
}
