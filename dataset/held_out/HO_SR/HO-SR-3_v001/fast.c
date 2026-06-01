#include <stdlib.h>
#include <string.h>

// FAST: allocate the same 120-byte struct on the STACK.  Stack memory
// is hot in L1, prefetched aggressively, and the 8 fields all land in
// the same 2 cache lines.  No malloc/free pair per iteration.
//
// The compiler cannot do this for the slow code because the struct
// pointer escapes via the cross-TU noinline init function -- escape
// analysis must conservatively assume the pointer is captured.
//
// Cite: Abseil Performance Tip #83 (2024-06-17).
#define HO_SR3_STRUCT_BYTES 120
#define HO_SR3_N_FIELDS 8

typedef struct {
    long long f0, f1, f2, f3, f4, f5, f6, f7;
    char _pad[HO_SR3_STRUCT_BYTES - HO_SR3_N_FIELDS * sizeof(long long)];
} HoSr3Stats;

extern void ho_sr3_init_struct_v001(HoSr3Stats *s, long seed);

long long fast_ho_sr3_v001(long n_instances) {
    long long total = 0;
    for (long i = 0; i < n_instances; i++) {
        HoSr3Stats s;          // stack allocation -- same size, no malloc
        ho_sr3_init_struct_v001(&s, i);
        long long sum = s.f0 + s.f1 + s.f2 + s.f3 + s.f4 + s.f5 + s.f6 + s.f7;
        long long prod = s.f0 * s.f1;
        total += sum + prod;
    }
    return total;
}
