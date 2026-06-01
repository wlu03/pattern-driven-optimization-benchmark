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
    /* Generate a deterministic mix of all 10 opcodes, with PUSH-arg bytes. */
    uint8_t *prog = (uint8_t*)malloc((size_t)N * 2);
    srand(45);
    size_t pos = 0;
    while (pos < (size_t)N * 2 - 2) {
        uint8_t op = (uint8_t)(rand() % 9);   /* avoid HALT in body */
        prog[pos++] = op;
        if (op == 0) prog[pos++] = (uint8_t)(rand() & 0xff);
    }
    prog[pos] = 9;  /* HALT */

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int64_t rs = slow_ho_cf2_v003(prog, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int64_t rf = fast_ho_cf2_v003(prog, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(prog);
    return correct ? 0 : 1;
}
