#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 100k instances; each slow iteration is one malloc + one free + 8 reads
// + 1 multiply.  malloc/free per-call is ~50-100 ns, whereas the field
// reduction on a stack struct (already hot in L1) is ~5 ns.  Total
// slow time should be dominated by allocator calls.
#define N_INSTANCES 200000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_slow = slow_ho_sr3_v002(N_INSTANCES);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_fast = fast_ho_sr3_v002(N_INSTANCES);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = ((long long)r_slow == (long long)r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}
