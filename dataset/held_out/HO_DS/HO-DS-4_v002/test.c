#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 4M buckets x 8B per pointer = 32 MB tagged_buckets array.  The
// underlying node pool is 256-byte-padded so the pool is ~1 GB, which
// dwarfs any LLC (M5 Pro: ~32 MB; Xeon: ~96 MB).  Pointers are
// permuted so each chase is a fresh DRAM miss for the slow path.
#define N 6000000
#define NQ 4           // 4 distinct query tags

#ifndef HO_DS4_NODE_DEFINED
#define HO_DS4_NODE_DEFINED
typedef struct {
    uint16_t fp;
    uint16_t _pad;
    int payload;
    char    _padding[248];   // 256-byte node so the pool spreads across DRAM
} HoDs4Node;
#endif

#define HO_DS4_TAG_SHIFT 48
#define HO_DS4_PTR_MASK  ((uintptr_t)0x0000FFFFFFFFFFFFULL)

// SLOW_CODE_HERE
// FAST_CODE_HERE

// Fisher-Yates so the pointer chase hits random nodes (not stride-1
// which the prefetcher would handle).
static void shuffle(long *a, long n) {
    for (long i = n - 1; i > 0; i--) {
        long j = (long)(((unsigned long long)rand() * (unsigned long long)rand()) % (i + 1));
        long t = a[i]; a[i] = a[j]; a[j] = t;
    }
}

int main() {
    HoDs4Node *pool = malloc(N * sizeof(HoDs4Node));
    HoDs4Node **buckets = malloc(N * sizeof(HoDs4Node *));
    uintptr_t *tagged = malloc(N * sizeof(uintptr_t));
    long *perm = malloc(N * sizeof(long));
    uint16_t *queries = malloc(NQ * sizeof(uint16_t));
    if (!pool || !buckets || !tagged || !perm || !queries) return 1;

    srand(44);
    for (long i = 0; i < N; i++) perm[i] = i;
    shuffle(perm, N);

    for (long i = 0; i < N; i++) {
        // 16-bit fingerprint: 8 distinct values over the pool, distributed
        // randomly.  Roughly 1/8th of entries match any given query.
        uint16_t tag = (uint16_t)(rand() & 0x7) + 1;  // 1..8
        pool[i].fp = tag;
        pool[i]._pad = 0;
        pool[i].payload = (int)(i & 0xFFFF);
    }
    for (long i = 0; i < N; i++) {
        HoDs4Node *target = &pool[perm[i]];   // scatter-shuffle pointer chase
        buckets[i] = target;
        uintptr_t p = (uintptr_t)target;
        tagged[i] = (p & HO_DS4_PTR_MASK)
                  | ((uintptr_t)target->fp << HO_DS4_TAG_SHIFT);
    }
    for (int q = 0; q < NQ; q++) queries[q] = (uint16_t)((q & 0x7) + 1);

    struct timespec t0, t1;
    long long slow_total = 0, fast_total = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int q = 0; q < NQ; q++)
        slow_total += slow_ho_ds4_v002(buckets, N, queries[q]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int q = 0; q < NQ; q++)
        fast_total += fast_ho_ds4_v002(tagged, N, queries[q]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (slow_total == fast_total);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(pool); free(buckets); free(tagged); free(perm); free(queries);
    return 0;
}
