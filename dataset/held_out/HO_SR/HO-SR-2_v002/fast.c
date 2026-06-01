#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// FAST: for 8-byte keys, replace xxh3-style avalanche with a
// specialized 1-instruction CRC32 + a multiplicative mix.  On x86-64
// with SSE4.2 this is `__builtin_ia32_crc32di(0, key) * KMUL`, ~5
// instructions in total.  On ARM64 we fall back to a multiplicative
// hash (~3 instructions), still much simpler than xxh3 though without
// the same speedup margin.
//
// Cite: Birler/Schmidt/Fent/Neumann CedarDB DaMoN'24 hash-table paper,
// Figure 8.
#define HO_SR2_CAP 8192

typedef struct { uint64_t key; long long value; int used; } HoSr2Entry;

static inline uint64_t ho_sr2_fast_hash(uint64_t k) {
#if defined(__SSE4_2__) && (defined(__x86_64__) || defined(_M_X64))
    return (uint64_t)__builtin_ia32_crc32di(0, k) * 0x2545F4914F6CDD1Dull;
#else
    // ARM64 / non-SSE4.2 fallback: two-multiply mix (Mulxsh32).  Still
    // ~3 ops vs xxh3's ~20.  Speedup smaller than on x86 but the
    // pattern (cross-algorithm hash substitution) is identical.
    uint64_t x = k * 0xbf58476d1ce4e5b9ull;
    x ^= x >> 31;
    return x * 0x94d049bb133111ebull;
#endif
}

long long fast_ho_sr2_v002(uint64_t *keys, long long *values, long n_kv,
                             uint64_t *queries, long nq) {
    HoSr2Entry *table = calloc(HO_SR2_CAP, sizeof(HoSr2Entry));
    if (!table) return 0;
    for (long i = 0; i < n_kv; i++) {
        uint64_t h = ho_sr2_fast_hash(keys[i]) & (HO_SR2_CAP - 1);
        while (table[h].used) h = (h + 1) & (HO_SR2_CAP - 1);
        table[h].key = keys[i];
        table[h].value = values[i];
        table[h].used = 1;
    }
    long long sum = 0;
    for (long i = 0; i < nq; i++) {
        uint64_t k = queries[i];
        uint64_t h = ho_sr2_fast_hash(k) & (HO_SR2_CAP - 1);
        while (table[h].used) {
            if (table[h].key == k) { sum += table[h].value; break; }
            h = (h + 1) & (HO_SR2_CAP - 1);
        }
    }
    free(table);
    return sum;
}
