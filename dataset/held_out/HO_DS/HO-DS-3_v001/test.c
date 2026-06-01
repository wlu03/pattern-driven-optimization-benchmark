#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define N 500000

#ifndef HO_DS3_WIDE_DEFINED
#define HO_DS3_WIDE_DEFINED
typedef struct {
    int64_t level;
    int64_t pad_a;
    int64_t pad_b;
    int64_t pad_c;
    int64_t pad_d;
    int64_t pad_e;
    int64_t pad_f;
    int64_t pad_g;
} HoDs3Wide;
#endif

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoDs3Wide *wide = malloc(N * sizeof(HoDs3Wide));
    uint8_t *narrow = malloc(N * sizeof(uint8_t));
    if (!wide || !narrow) return 1;

    for (long i = 0; i < N; i++) {
        uint8_t v = (uint8_t)(i & 0xFF);
        wide[i].level = v;
        wide[i].pad_a = wide[i].pad_b = wide[i].pad_c = wide[i].pad_d =
        wide[i].pad_e = wide[i].pad_f = wide[i].pad_g = 0;
        narrow[i] = v;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_slow = slow_ho_ds3_v001(wide, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_fast = fast_ho_ds3_v001(narrow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = ((long long)r_slow == (long long)r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(wide); free(narrow);
    return 0;
}
