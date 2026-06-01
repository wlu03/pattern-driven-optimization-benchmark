#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// FAST: Count-Min Sketch (Cormode & Muthukrishnan 2003) with width
// w=2048 and depth d=5.  Update touches d=5 cells (one per row); query
// returns the minimum across d cells.  CMS is a one-sided estimator
// (always >= true count); error bound is e*N/w with prob 1-e^-d.
// For w=2048, d=5, N=1M, eps ~= 0.0013 -> per-query error well under
// 5% relative for any key whose true count >= 1% of N.
//
// O(w*d) = O(10240) memory total (40 KB at int32) regardless of N.
// Inner update is 5 mults + 5 adds + 5 max -- vectorizable.
//
// Cite: Cormode & Muthukrishnan, "An Improved Data Stream Summary:
// The Count-Min Sketch and its Applications" (LATIN 2004 / J. Alg
// 2005).  arXiv:cs/0312050.
#define HO_AL3_W    2048
#define HO_AL3_D    5
#define HO_AL3_MASK (HO_AL3_W - 1)

// Five pairwise-independent hash multipliers (odd 64-bit constants).
static const uint64_t ho_al3_mul[HO_AL3_D] = {
    0x9E3779B97F4A7C15ULL,
    0xBF58476D1CE4E5B9ULL,
    0x94D049BB133111EBULL,
    0xC6BC279692B5C323ULL,
    0xFF51AFD7ED558CCDULL,
};
static const uint64_t ho_al3_add[HO_AL3_D] = {
    0x6A09E667F3BCC908ULL,
    0xBB67AE8584CAA73BULL,
    0x3C6EF372FE94F82BULL,
    0xA54FF53A5F1D36F1ULL,
    0x510E527FADE682D1ULL,
};

static inline uint32_t ho_al3_hash(uint32_t k, int r) {
    uint64_t x = (uint64_t)k * ho_al3_mul[r] + ho_al3_add[r];
    x ^= x >> 31;
    return (uint32_t)(x & HO_AL3_MASK);
}

long long fast_ho_al3_v002(uint32_t *keys, int32_t *incs, long n,
                              uint32_t *query_keys, long nq,
                              int64_t *out_freqs) {
    int64_t *cms = calloc(HO_AL3_W * HO_AL3_D, sizeof(int64_t));
    if (!cms) return 0;

    for (long i = 0; i < n; i++) {
        uint32_t k = keys[i];
        int32_t v = incs[i];
        for (int r = 0; r < HO_AL3_D; r++) {
            uint32_t h = ho_al3_hash(k, r);
            cms[r * HO_AL3_W + h] += v;
        }
    }

    long long sum = 0;
    for (long q = 0; q < nq; q++) {
        uint32_t k = query_keys[q];
        int64_t best = cms[ho_al3_hash(k, 0)];
        for (int r = 1; r < HO_AL3_D; r++) {
            int64_t v = cms[r * HO_AL3_W + ho_al3_hash(k, r)];
            if (v < best) best = v;
        }
        out_freqs[q] = best;
        sum += best;
    }

    free(cms);
    return sum;
}
