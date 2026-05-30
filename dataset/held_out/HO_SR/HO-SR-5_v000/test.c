#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// Many calls with non-zero x (so the slow path's compiler-rewritten
// branch+memcpy hits the "copy" branch every call -- the fast path
// must still execute the unconditional masked-OR scan).  The
// inverted-framing pattern means slow's wall-clock may be lower
// because memcpy is faster than per-byte masked OR.  See metadata.json
// novelty_rationale for the full explanation.
#define LEN      64
#define N_CALLS  1000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint8_t *dst_slow = malloc(LEN);
    uint8_t *dst_fast = malloc(LEN);
    uint8_t *src      = malloc(LEN);
    if (!dst_slow || !dst_fast || !src) return 1;

    // Two distinguishable patterns so we can verify the copy happened.
    memset(dst_slow, 0xAA, LEN);
    memset(dst_fast, 0xAA, LEN);
    for (int i = 0; i < LEN; i++) src[i] = (uint8_t)(i + 1);

    int x = 1;   // non-zero -> copy

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) {
        // Reset dst before each call to keep the workload deterministic.
        memset(dst_slow, 0xAA, LEN);
        slow_ho_sr5_v000(dst_slow, src, x, LEN);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) {
        memset(dst_fast, 0xAA, LEN);
        fast_ho_sr5_v000(dst_fast, src, x, LEN);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Correctness: with x != 0 both should copy src into dst.
    int correct = (memcmp(dst_slow, src, LEN) == 0) &&
                  (memcmp(dst_fast, src, LEN) == 0);
    // Also try x == 0 (no-copy branch).
    memset(dst_slow, 0xAA, LEN);
    memset(dst_fast, 0xAA, LEN);
    slow_ho_sr5_v000(dst_slow, src, 0, LEN);
    fast_ho_sr5_v000(dst_fast, src, 0, LEN);
    for (int i = 0; i < LEN; i++) {
        if (dst_slow[i] != 0xAA) correct = 0;
        if (dst_fast[i] != 0xAA) correct = 0;
    }

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(dst_slow); free(dst_fast); free(src);
    return 0;
}
