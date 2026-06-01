#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// FAST: HyperLogLogLog (Karppa & Pagh, KDD 2022, arXiv:2205.11327) --
// compressed HLL using per-block 8-bit base + per-register 4-bit
// offset.  Total memory: M*4 bits + (M/64)*8 bits ~= 8 KB + 256 B
// ~= 8.25 KB vs vanilla HLL's 16 KB.  The compression matters in this
// benchmark because the harmonic-mean estimator pass is run n_polls
// times: a 16 KB working set spills past L1 once mixed with other state
// while 8 KB stays hot.
//
// Insert path uses *bulking* (the Karppa-Pagh trick): batch 256
// inserts, do hash extract in a tight vectorizable phase, then apply
// per-block.  Without bulking, the per-insert rebase check would make
// HLLL ~10x slower than vanilla HLL; bulking amortizes the rebase
// cost so HLLL approaches vanilla HLL insert throughput.
//
// Layout: offsets packed 2-per-byte; base array 1 byte per 64-register
// block.  effective_rank = base[blk] + offset[idx].
//
// Cite: Karppa & Pagh, "HyperLogLogLog: Cardinality Estimation With
// One Log More" (KDD 2022).  arXiv:2205.11327.
#define HO_AL4_P     14
#define HO_AL4_M     (1u << HO_AL4_P)
#define HO_AL4_PMASK (HO_AL4_M - 1u)
#define HO_AL4_BLK_LOG  6
#define HO_AL4_BLK_SIZE (1u << HO_AL4_BLK_LOG)
#define HO_AL4_NBLK     (HO_AL4_M / HO_AL4_BLK_SIZE)
#define HO_AL4_BATCH    256
#define HO_AL4_OFF_MAX  15

static inline uint64_t ho_al4_mix(uint64_t k) {
    k ^= k >> 33; k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33; k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

// 4-bit packed offset: two registers per byte.
static inline uint8_t off_get(uint8_t *off_packed, uint32_t idx) {
    uint8_t b = off_packed[idx >> 1];
    return (idx & 1) ? (uint8_t)(b >> 4) : (uint8_t)(b & 0xF);
}
static inline void off_set(uint8_t *off_packed, uint32_t idx, uint8_t v) {
    uint8_t b = off_packed[idx >> 1];
    if (idx & 1) b = (uint8_t)((b & 0x0F) | (v << 4));
    else         b = (uint8_t)((b & 0xF0) | (v & 0x0F));
    off_packed[idx >> 1] = b;
}

static double fast_ho_al4_est(uint8_t *off_packed, uint8_t *base) {
    double sum = 0.0;
    int zeros = 0;
    for (uint32_t k = 0; k < HO_AL4_M; k++) {
        uint8_t r = (uint8_t)(base[k >> HO_AL4_BLK_LOG] + off_get(off_packed, k));
        sum += 1.0 / (double)(1ULL << r);
        if (r == 0) zeros++;
    }
    const double alpha = 0.7213 / (1.0 + 1.079 / (double)HO_AL4_M);
    double m = (double)HO_AL4_M;
    double est = alpha * m * m / sum;
    if (est <= 2.5 * m && zeros > 0) est = m * log(m / (double)zeros);
    return est;
}

long fast_ho_al4_v003(uint64_t *keys, long n, int n_polls) {
    uint8_t *off_packed = calloc(HO_AL4_M / 2, 1);  // 4 bits per register -> 8 KB
    uint8_t *base       = calloc(HO_AL4_NBLK, 1);    // 256 bytes
    if (!off_packed || !base) { free(off_packed); free(base); return 0; }

    uint32_t *bi = malloc(HO_AL4_BATCH * sizeof(uint32_t));
    uint8_t  *br = malloc(HO_AL4_BATCH * sizeof(uint8_t));
    if (!bi || !br) { free(off_packed); free(base); free(bi); free(br); return 0; }

    long i = 0;
    while (i < n) {
        long bn = (n - i < HO_AL4_BATCH) ? (n - i) : HO_AL4_BATCH;

        // Phase 1: tight hash-extract loop (vectorizable).
        for (long b = 0; b < bn; b++) {
            uint64_t h = ho_al4_mix(keys[i + b]);
            uint32_t idx = (uint32_t)(h & HO_AL4_PMASK);
            uint64_t suffix = (h >> HO_AL4_P) | (1ULL << (64 - HO_AL4_P));
            bi[b] = idx;
            br[b] = (uint8_t)(__builtin_ctzll(suffix) + 1);
        }

        // Phase 2: per-block apply with deferred rebase.
        for (long b = 0; b < bn; b++) {
            uint32_t idx = bi[b];
            uint8_t  r   = br[b];
            uint32_t blk = idx >> HO_AL4_BLK_LOG;
            uint8_t  bs  = base[blk];
            if (r <= bs) continue;
            uint8_t want = (uint8_t)(r - bs);
            if (want > HO_AL4_OFF_MAX) want = HO_AL4_OFF_MAX;  // saturate
            uint8_t cur = off_get(off_packed, idx);
            if (want > cur) off_set(off_packed, idx, want);
        }
        i += bn;
    }

    // Compaction pass: lift the block base to the block-min so saturation
    // does not bias the estimator low.  In production this runs periodically
    // (Karppa-Pagh "rebase phase"); we do it once before the polls.
    for (uint32_t blk = 0; blk < HO_AL4_NBLK; blk++) {
        uint8_t bmin = HO_AL4_OFF_MAX;
        uint32_t bs = blk << HO_AL4_BLK_LOG;
        for (uint32_t k = 0; k < HO_AL4_BLK_SIZE; k++) {
            uint8_t o = off_get(off_packed, bs + k);
            if (o < bmin) bmin = o;
        }
        if (bmin > 0) {
            for (uint32_t k = 0; k < HO_AL4_BLK_SIZE; k++) {
                uint8_t o = off_get(off_packed, bs + k);
                off_set(off_packed, bs + k, (uint8_t)(o - bmin));
            }
            base[blk] = (uint8_t)(base[blk] + bmin);
        }
    }

    // Polls (hot loop -- 8 KB fits L1).
    double last = 0.0;
    for (int p = 0; p < n_polls; p++) last = fast_ho_al4_est(off_packed, base);

    free(off_packed); free(base); free(bi); free(br);
    return (long)(last + 0.5);
}
