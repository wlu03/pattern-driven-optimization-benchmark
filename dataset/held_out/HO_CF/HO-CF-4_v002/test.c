#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define N_SYMS 1000000
#define N_BYTES ((N_SYMS * 5 + 7) / 8)
#define PAD 16

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main(void) {
    uint8_t *src = (uint8_t*)calloc((size_t)(N_BYTES + PAD), 1);
    srand(44);
    for (int i = 0; i < N_BYTES; i++) src[i] = (uint8_t)(rand() & 0xff);
    /* Last PAD bytes left as zeros so fast version's 8-byte refill is safe. */

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rs = slow_ho_cf4_v002(src, N_BYTES, N_SYMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rf = fast_ho_cf4_v002(src, N_BYTES, N_SYMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(src);
    return correct ? 0 : 1;
}
