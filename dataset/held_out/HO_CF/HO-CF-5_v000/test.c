#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main(void) {
    uint8_t *input = (uint8_t*)malloc((size_t)N);
    uint8_t *out_s = (uint8_t*)malloc((size_t)N);
    uint8_t *out_f = (uint8_t*)malloc((size_t)N);
    srand(42);
    for (int i = 0; i < N; i++) input[i] = (uint8_t)(rand() & 0xff);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rs = slow_ho_cf5_v000(input, N, out_s);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rf = fast_ho_cf5_v000(input, N, out_f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    int correct = (rs == rf) && (memcmp(out_s, out_f, (size_t)N) == 0);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(input); free(out_s); free(out_f);
    return correct ? 0 : 1;
}
