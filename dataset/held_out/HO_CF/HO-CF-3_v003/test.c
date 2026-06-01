#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define N 2000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main(void) {
    int32_t *rc_in = (int32_t*)malloc((size_t)N * sizeof(int32_t));
    int32_t *rc_s  = (int32_t*)malloc((size_t)N * sizeof(int32_t));
    int32_t *rc_f  = (int32_t*)malloc((size_t)N * sizeof(int32_t));
    srand(45);
    for (int i = 0; i < N; i++) rc_in[i] = rand() & 0xffff;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_cf3_v003(rc_s, rc_in, N, 7);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_cf3_v003(rc_f, rc_in, N, 7);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    int correct = (memcmp(rc_s, rc_f, (size_t)N * sizeof(int32_t)) == 0);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(rc_in); free(rc_s); free(rc_f);
    return correct ? 0 : 1;
}
