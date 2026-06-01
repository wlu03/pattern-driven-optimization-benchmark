#include <stdlib.h>
#include <string.h>

// SLOW: allocate a 120-byte stats struct on the heap, populate it via a
// cross-TU noinline init function, then read its 8 fields in a hot
// reduction loop.  The heap allocation places the struct at an
// unpredictable address -- the read of each field may straddle a fresh
// cache line, and tcmalloc/jemalloc-style allocators interleave
// allocations from different sizeclasses so prefetch is poor.
//
// The compiler has heap-elision passes (LLVM, GCC) but they fail to
// fire here because:
//   (1) the struct pointer escapes via the cross-TU init_struct() call;
//   (2) the init function is noinline + lives in helper.c;
//   (3) the struct is large (>64 bytes) so most heuristics decline.
//
// Cite: Abseil Performance Tip #83 (2024-06-17): "stats_info was only
// 120 bytes, so accessing its fields from data.stats_info might entail
// 4 cachelines."
#define HO_SR3_STRUCT_BYTES 120
#define HO_SR3_N_FIELDS 8

typedef struct {
    long long f0, f1, f2, f3, f4, f5, f6, f7;
    char _pad[HO_SR3_STRUCT_BYTES - HO_SR3_N_FIELDS * sizeof(long long)];
} HoSr3Stats;

extern void ho_sr3_init_struct_v002(HoSr3Stats *s, long seed);

long long slow_ho_sr3_v002(long n_instances) {
    long long total = 0;
    for (long i = 0; i < n_instances; i++) {
        HoSr3Stats *s = malloc(sizeof(HoSr3Stats));
        ho_sr3_init_struct_v002(s, i);
        long long sum = s->f0 + s->f1 + s->f2 + s->f3 + s->f4 + s->f5 + s->f6 + s->f7;
        long long prod = s->f0 * s->f1;  // small extra reduction
        total += sum + prod;
        free(s);
    }
    return total;
}
