#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// SLOW: hash table using xxh3-style multi-round avalanche hash on every
// 8-byte key.  The xxh3-style mixer does 4 multiplications + 6 shifts
// + 2 xors per key -- ~20 instructions on x86 and ~30 on ARM -- and
// the compiler cannot CSE across calls because the input changes.
// In a tight insert/lookup loop, hashing dominates over the table walk.
#define HO_SR2_CAP 8192

typedef struct { uint64_t key; long long value; int used; } HoSr2Entry;

extern uint64_t ho_sr2_xxh3_hash_v000(uint64_t k);

long long slow_ho_sr2_v000(uint64_t *keys, long long *values, long n_kv,
                             uint64_t *queries, long nq) {
    HoSr2Entry *table = calloc(HO_SR2_CAP, sizeof(HoSr2Entry));
    if (!table) return 0;
    for (long i = 0; i < n_kv; i++) {
        uint64_t h = ho_sr2_xxh3_hash_v000(keys[i]) & (HO_SR2_CAP - 1);
        while (table[h].used) h = (h + 1) & (HO_SR2_CAP - 1);
        table[h].key = keys[i];
        table[h].value = values[i];
        table[h].used = 1;
    }
    long long sum = 0;
    for (long i = 0; i < nq; i++) {
        uint64_t k = queries[i];
        uint64_t h = ho_sr2_xxh3_hash_v000(k) & (HO_SR2_CAP - 1);
        while (table[h].used) {
            if (table[h].key == k) { sum += table[h].value; break; }
            h = (h + 1) & (HO_SR2_CAP - 1);
        }
    }
    free(table);
    return sum;
}
