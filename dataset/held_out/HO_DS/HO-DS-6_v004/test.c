#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define HO_DS6_N_REG  16384

// Workload: pre-generate 16384 6-bit values, then for each layout
// (slow=16 KB, fast=12 KB) populate and run N_POLLS estimator passes.
// The pattern's PRIMARY win is the 25% memory saving (16 KB -> 12 KB).
// The unpacking arithmetic adds a few cycles per get; in this
// microbenchmark fast may be SLOWER than slow at -O3 because both
// layouts fit in L1.  The success metric here is correct=1: that the
// model produced a working cross-byte 6-bit packed layout matching the
// Redis HLL_DENSE_GET_REGISTER scheme.
#define N_POLLS 5000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint8_t *vals       = malloc(HO_DS6_N_REG);
    uint8_t *regs_slow  = calloc(HO_DS6_N_REG, 1);            // 16 KB
    uint8_t *regs_fast  = calloc(HO_DS6_N_REG * 6 / 8 + 8, 1); // 12 KB + slack
    if (!vals || !regs_slow || !regs_fast) return 1;

    // HLL-ish rank distribution.
    uint64_t s = 0x12345678ULL;
    for (uint32_t i = 0; i < HO_DS6_N_REG; i++) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        uint8_t r = 0;
        uint64_t bits = s;
        while (r < 30 && (bits & 1)) { r++; bits >>= 1; }
        vals[i] = (uint8_t)(3 + (r % 10));
    }

    struct timespec t0, t1;
    int zeros_s = 0, zeros_f = 0;
    double sum_s = 0, sum_f = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    sum_s = slow_ho_ds6_v004(vals, regs_slow, N_POLLS, &zeros_s);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    sum_f = fast_ho_ds6_v004(vals, regs_fast, N_POLLS, &zeros_f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (zeros_s == zeros_f) &&
                  (fabs(sum_s - sum_f) / fmax(fabs(sum_s), 1e-12) < 1e-9);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(vals); free(regs_slow); free(regs_fast);
    return 0;
}
