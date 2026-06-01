#include <stdlib.h>

#define HO_SR3_STRUCT_BYTES 120
#define HO_SR3_N_FIELDS 8

typedef struct {
    long long f0, f1, f2, f3, f4, f5, f6, f7;
    char _pad[HO_SR3_STRUCT_BYTES - HO_SR3_N_FIELDS * sizeof(long long)];
} HoSr3Stats;

// Cross-TU + noinline init function.  This is what escape analysis
// cannot see through: the compiler must assume `s` might be captured
// for arbitrary later use, so it cannot elide the heap allocation in
// the slow path.
__attribute__((noinline))
void ho_sr3_init_struct_v004(HoSr3Stats *s, long seed) {
    s->f0 = seed;
    s->f1 = seed + 1;
    s->f2 = seed + 2;
    s->f3 = seed + 3;
    s->f4 = seed + 4;
    s->f5 = seed + 5;
    s->f6 = seed + 6;
    s->f7 = seed + 7;
}
