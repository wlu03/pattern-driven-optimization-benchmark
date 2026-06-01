#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// SLOW: exact distinct-count using a chained hash set.  N=10^6 insert
// operations populate buckets of HoAl2Node*, then we walk every bucket
// once to count distinct keys.  O(N) time *and* O(N) memory --- ~16MB
// of node allocations for 1M unique keys plus per-insert pointer
// chasing and malloc cost.
//
// Reference baseline for the HyperLogLog comparison (antirez 2014;
// HLL in Redis at < 1% error with a 12 KB fixed footprint).
#define HO_AL2_CAP (1u << 20)   // 1M buckets, 1:1 load factor

typedef struct HoAl2Node {
    uint64_t key;
    struct HoAl2Node *next;
} HoAl2Node;

long slow_ho_al2_v004(uint64_t *keys, long n) {
    HoAl2Node **table = calloc(HO_AL2_CAP, sizeof(HoAl2Node *));
    if (!table) return 0;
    long distinct = 0;
    for (long i = 0; i < n; i++) {
        uint64_t k = keys[i];
        // splitmix64 for bucket selection (kept inline; cheap)
        uint64_t h = k;
        h ^= h >> 30; h *= 0xbf58476d1ce4e5b9ULL;
        h ^= h >> 27; h *= 0x94d049bb133111ebULL;
        h ^= h >> 31;
        size_t b = (size_t)(h & (HO_AL2_CAP - 1));
        HoAl2Node *p = table[b];
        int found = 0;
        while (p) {
            if (p->key == k) { found = 1; break; }
            p = p->next;
        }
        if (!found) {
            HoAl2Node *nn = malloc(sizeof(HoAl2Node));
            nn->key = k;
            nn->next = table[b];
            table[b] = nn;
            distinct++;
        }
    }
    // Free everything
    for (size_t b = 0; b < HO_AL2_CAP; b++) {
        HoAl2Node *p = table[b];
        while (p) { HoAl2Node *nx = p->next; free(p); p = nx; }
    }
    free(table);
    return distinct;
}
