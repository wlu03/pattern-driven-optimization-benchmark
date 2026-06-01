#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 32 message bytes -> 256 polynomial coefficients (the ML-KEM message
// length).  N_CALLS calls in the timing loop.  Inverted-framing
// pattern: slow's compiler-introduced branch may be FASTER in
// wall-clock (depending on branch prediction), but it leaks the
// message bits via timing.  See metadata.json novelty_rationale.
#define N_BYTES   32
#define N_COEFFS  (N_BYTES * 8)
#define N_CALLS   200000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint8_t *msg     = malloc(N_BYTES);
    int16_t *r_slow  = malloc(N_COEFFS * sizeof(int16_t));
    int16_t *r_fast  = malloc(N_COEFFS * sizeof(int16_t));
    if (!msg || !r_slow || !r_fast) return 1;

    // Deterministic non-trivial message.
    for (int i = 0; i < N_BYTES; i++) msg[i] = (uint8_t)(0x5A ^ (i * 17));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) slow_ho_sr6_v003(msg, r_slow, N_BYTES);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) fast_ho_sr6_v003(msg, r_fast, N_BYTES);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Correctness: both must produce the same 256 coefficients.
    int correct = 1;
    for (int k = 0; k < N_COEFFS; k++) {
        if (r_slow[k] != r_fast[k]) { correct = 0; break; }
        int16_t expected = ((msg[k / 8] >> (k & 7)) & 1) ? 1665 : 0;
        if (r_slow[k] != expected) { correct = 0; break; }
    }

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(msg); free(r_slow); free(r_fast);
    return 0;
}
