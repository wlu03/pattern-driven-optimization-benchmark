#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 30, k = 15;
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = 100000;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_v009(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_v009(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}
