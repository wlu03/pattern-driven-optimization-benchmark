#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// SLOW: exact frequency-count using a chained hash-map<int, int>.
// Inserts (key, increment) pairs into a 16K-bucket table; queries the
// frequency of K hot keys after all inserts.  O(N) memory grows with
// the number of distinct keys.  Hash-map probes + heap node walks make
// the insert loop ~3-10x more expensive per op than a small array.
#define HO_AL3_CAP (1u << 16)   // 64K buckets

typedef struct HoAl3Node {
    uint32_t key;
    int64_t  count;
    struct HoAl3Node *next;
} HoAl3Node;

static inline uint64_t ho_al3_mix(uint64_t k) {
    k ^= k >> 33; k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33; k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

long long slow_ho_al3_v000(uint32_t *keys, int32_t *incs, long n,
                              uint32_t *query_keys, long nq,
                              int64_t *out_freqs) {
    HoAl3Node **table = calloc(HO_AL3_CAP, sizeof(HoAl3Node *));
    if (!table) return 0;

    for (long i = 0; i < n; i++) {
        uint32_t k = keys[i];
        size_t b = (size_t)(ho_al3_mix(k) & (HO_AL3_CAP - 1));
        HoAl3Node *p = table[b];
        while (p) {
            if (p->key == k) { p->count += incs[i]; break; }
            p = p->next;
        }
        if (!p) {
            HoAl3Node *nn = malloc(sizeof(HoAl3Node));
            nn->key = k; nn->count = incs[i]; nn->next = table[b];
            table[b] = nn;
        }
    }

    // Answer the queries: exact frequency of each query key.
    long long sum = 0;
    for (long q = 0; q < nq; q++) {
        uint32_t k = query_keys[q];
        size_t b = (size_t)(ho_al3_mix(k) & (HO_AL3_CAP - 1));
        HoAl3Node *p = table[b];
        int64_t f = 0;
        while (p) {
            if (p->key == k) { f = p->count; break; }
            p = p->next;
        }
        out_freqs[q] = f;
        sum += f;
    }

    for (size_t b = 0; b < HO_AL3_CAP; b++) {
        HoAl3Node *p = table[b];
        while (p) { HoAl3Node *nx = p->next; free(p); p = nx; }
    }
    free(table);
    return sum;
}
