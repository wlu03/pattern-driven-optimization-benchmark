#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 100k blocks total (a multiple of 8 so the fast path consumes them all).
// 100k * 36 B = 3.6 MB AoS;  12.5k * 288 B = 3.6 MB Kx8 SoA.  Both fit
// in L2 (per-iteration measurement is the inner SIMD throughput), so
// the speedup comes from the inner-loop vectorization width — not from
// raw bandwidth.
#define N_BLOCKS 800000
#define REPS 5

#ifndef HO_DS5_BLOCK_DEFINED
#define HO_DS5_BLOCK_DEFINED
typedef struct {
    float   scale;
    uint8_t qs[32];
} HoDs5Block;
#endif

#ifndef HO_DS5_BLOCK8_DEFINED
#define HO_DS5_BLOCK8_DEFINED
typedef struct {
    float   scales[8];
    uint8_t qs[8 * 32];
} HoDs5Block8;
#endif

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoDs5Block  *aos = malloc(N_BLOCKS * sizeof(HoDs5Block));
    HoDs5Block8 *soa = malloc((N_BLOCKS / 8) * sizeof(HoDs5Block8));
    if (!aos || !soa) return 1;

    srand(45);
    for (long b = 0; b < N_BLOCKS; b++) {
        float s = 0.1f + (float)(b % 13) * 0.001f;
        aos[b].scale = s;
        for (int i = 0; i < 32; i++) {
            uint8_t q = (uint8_t)((b * 31 + i * 7) & 0xFF);
            aos[b].qs[i] = q;
        }
    }
    // Mirror AoS into Kx8 SoA so both produce the same dequant sum.
    // Note the transpose: SoA qs is indexed as qs[quant_index * 8 + block]
    // so that the fast kernel's inner loop over `k` (block-within-super)
    // becomes a unit-stride 8-byte SIMD load.
    for (long s = 0; s < N_BLOCKS / 8; s++) {
        for (int k = 0; k < 8; k++) {
            soa[s].scales[k] = aos[s * 8 + k].scale;
        }
        for (int i = 0; i < 32; i++) {
            for (int k = 0; k < 8; k++) {
                soa[s].qs[i * 8 + k] = aos[s * 8 + k].qs[i];
            }
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = 0;
    for (int r = 0; r < REPS; r++) r_slow += slow_ho_ds5_v003(aos, N_BLOCKS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = 0;
    for (int r = 0; r < REPS; r++) r_fast += fast_ho_ds5_v003(soa, N_BLOCKS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(aos); free(soa);
    return 0;
}
