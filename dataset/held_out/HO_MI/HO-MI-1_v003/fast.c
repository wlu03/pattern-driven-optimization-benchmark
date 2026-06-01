// Same list, but indexed.  The caller pre-computed the full traversal
// order as an array of indices into the slab; that array is dense and
// streams-friendly.  We can therefore peek several steps ahead and
// issue software prefetches for the corresponding slab entries while
// the current entry's DRAM fetch is still in flight.
typedef struct HoMi1Node {
    long value;
    struct HoMi1Node *next;
    char _pad[240];
} HoMi1Node;

#define PREFETCH_AHEAD 16

long long fast_ho_mi1_v003(HoMi1Node *slab, long *next_index, long n) {
    long long sum = 0;
    // Warm up: prefetch the first PREFETCH_AHEAD nodes.
    for (long i = 0; i < PREFETCH_AHEAD && i < n; i++)
        __builtin_prefetch(&slab[next_index[i]], 0, 0);
    for (long i = 0; i < n; i++) {
        if (i + PREFETCH_AHEAD < n)
            __builtin_prefetch(&slab[next_index[i + PREFETCH_AHEAD]], 0, 0);
        sum += slab[next_index[i]].value;
    }
    return sum;
}
