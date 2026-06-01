#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 500k nodes * 256 B/node = ~128 MB working set -- well beyond L3 on
// commodity hardware.  Pointer-chase traversal serializes one DRAM
// round-trip per node.
#define N 250000

typedef struct HoMi1Node {
    long value;
    struct HoMi1Node *next;
    char _pad[240];
} HoMi1Node;

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoMi1Node *slab = malloc((size_t)N * sizeof(HoMi1Node));
    long *order = malloc((size_t)N * sizeof(long));
    if (!slab || !order) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (long i = 0; i < N; i++) order[i] = i;
    srand(43);
    for (long i = N - 1; i > 0; i--) {
        long j = rand() % (i + 1);
        long t = order[i]; order[i] = order[j]; order[j] = t;
    }
    for (long i = 0; i < N; i++) {
        slab[i].value = i + 1;
        memset(slab[i]._pad, 0, sizeof(slab[i]._pad));
    }
    // Chain: slab[order[0]] -> slab[order[1]] -> ... -> slab[order[N-1]]
    for (long i = 0; i < N - 1; i++) slab[order[i]].next = &slab[order[i + 1]];
    slab[order[N - 1]].next = (HoMi1Node *)0;
    HoMi1Node *head = &slab[order[0]];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_ho_mi1_v001(head, order, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_ho_mi1_v001(slab, order, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(slab); free(order);
    return 0;
}
