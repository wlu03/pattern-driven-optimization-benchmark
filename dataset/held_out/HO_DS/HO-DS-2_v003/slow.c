#include <stdlib.h>
#include <string.h>

// Open-addressed hash table using a "cryptographic-quality" mixing hash
// implemented in a separate TU (noinline).  This mirrors the common
// pattern of an std::unordered_map / HashMap whose hasher cannot be
// inlined by the compiler.  For a dictionary of just 12 entries, the
// per-lookup hashing cost dominates.
#define HO_DS2_CAP 32

extern unsigned int ho_ds2_strong_hash_v003(int k);

typedef struct { int key; int value; int used; } HoDs2Entry;

long long slow_ho_ds2_v003(int *keys, int *values, int n_kv,
                            int *queries, int nq) {
    HoDs2Entry table[HO_DS2_CAP];
    memset(table, 0, sizeof(table));
    for (int i = 0; i < n_kv; i++) {
        unsigned int h = ho_ds2_strong_hash_v003(keys[i]) % HO_DS2_CAP;
        while (table[h].used) h = (h + 1) % HO_DS2_CAP;
        table[h].key = keys[i]; table[h].value = values[i]; table[h].used = 1;
    }
    long long sum = 0;
    for (int i = 0; i < nq; i++) {
        int k = queries[i];
        unsigned int h = ho_ds2_strong_hash_v003(k) % HO_DS2_CAP;
        while (table[h].used) {
            if (table[h].key == k) { sum += table[h].value; break; }
            h = (h + 1) % HO_DS2_CAP;
        }
    }
    return sum;
}
