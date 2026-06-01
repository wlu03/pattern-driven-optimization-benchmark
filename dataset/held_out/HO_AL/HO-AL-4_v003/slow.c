#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// SLOW: standard HyperLogLog with m=16384 8-bit registers (16 KB).
// In a streaming workload that mixes inserts with repeated cardinality
// estimates (e.g., dashboards that poll a counter many times between
// inserts), the estimator pass walks all 16 KB of register state to
// compute the harmonic mean -- which spills past most CPUs' 32 KB L1
// once shared with other working set.  This is the natural HLL
// throughput baseline that the Karppa & Pagh HLLL compression
// improves on.
//
// Reference baseline for the Karppa & Pagh "HyperLogLogLog" compressed
// HLL (KDD 2022, arXiv:2205.11327).
#define HO_AL4_P     14
#define HO_AL4_M     (1u << HO_AL4_P)
#define HO_AL4_PMASK (HO_AL4_M - 1u)

static inline uint64_t ho_al4_slow_mix(uint64_t k) {
    k ^= k >> 33; k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33; k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

static inline double slow_ho_al4_est(uint8_t *reg) {
    double sum = 0.0;
    int zeros = 0;
    for (uint32_t i = 0; i < HO_AL4_M; i++) {
        sum += 1.0 / (double)(1ULL << reg[i]);
        if (reg[i] == 0) zeros++;
    }
    const double alpha = 0.7213 / (1.0 + 1.079 / (double)HO_AL4_M);
    double m = (double)HO_AL4_M;
    double est = alpha * m * m / sum;
    if (est <= 2.5 * m && zeros > 0) est = m * log(m / (double)zeros);
    return est;
}

long slow_ho_al4_v003(uint64_t *keys, long n, int n_polls) {
    uint8_t *reg = calloc(HO_AL4_M, 1);
    if (!reg) return 0;

    for (long i = 0; i < n; i++) {
        uint64_t h = ho_al4_slow_mix(keys[i]);
        uint32_t idx = (uint32_t)(h & HO_AL4_PMASK);
        uint64_t suffix = (h >> HO_AL4_P) | (1ULL << (64 - HO_AL4_P));
        int rank = __builtin_ctzll(suffix) + 1;
        if ((uint8_t)rank > reg[idx]) reg[idx] = (uint8_t)rank;
    }

    // Repeated cardinality polls -- the workload that exposes the
    // register-array memory pressure that HLLL compression alleviates.
    double last = 0.0;
    for (int p = 0; p < n_polls; p++) last = slow_ho_al4_est(reg);
    free(reg);
    return (long)(last + 0.5);
}
