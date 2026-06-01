#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define HO_IS5_NBITS    11
#define HO_IS5_TBL_SIZE (1u << HO_IS5_NBITS)

#ifndef HO_IS5_ENTRY_DEFINED
#define HO_IS5_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoIs5Entry;
#endif

// Many small decodes (the workload where the 14-byte safety margin
// hurts disproportionately): 100K decode calls, each producing 200
// symbols.  Slow's ilimit=src+14 forces the fast loop to drop into
// the slow per-symbol path 14 bytes early on EVERY call -- a ~28%
// throughput hit per zstd PR #3827.
#define N_DECODES   100000
#define N_PER_DEC   200

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoIs5Entry *table = malloc(HO_IS5_TBL_SIZE * sizeof(HoIs5Entry));
    for (uint32_t i = 0; i < HO_IS5_TBL_SIZE; i++) {
        table[i].sym   = (uint8_t)(i & 0xFF);
        uint8_t nb = 11;
        if ((i & 7) == 0)      nb = 4;
        else if ((i & 3) == 0) nb = 8;
        table[i].nbits = nb;
    }

    // Per-decode source: enough bytes to decode N_PER_DEC symbols at avg
    // ~10 bits each (since most entries are 11 bits, a few 8, a few 4)
    // = ~250 bytes + 16 padding for safe over-read.
    // src_len chosen so the slow's SAFETY margin (120 bytes) bites:
    // we need src_len = (bytes-needed-for-N_PER_DEC-symbols) + small
    // padding for over-read, so the conservative ilimit = src_len-SAFETY
    // forces ~SAFETY bytes-worth of tail symbols into the slow path.
    long src_len = (N_PER_DEC * HO_IS5_NBITS + 7) / 8 + 16;
    uint8_t *src = malloc(src_len);
    uint64_t st = 0x12345678ULL;
    for (long i = 0; i < src_len; i++) {
        st = st * 6364136223846793005ULL + 1442695040888963407ULL;
        src[i] = (uint8_t)(st >> 24);
    }

    uint8_t *dst_slow = malloc(N_PER_DEC);
    uint8_t *dst_fast = malloc(N_PER_DEC);
    // Sanity-check correctness once on a single decode before the timing loop.
    slow_ho_is5_v004(src, src_len, table, dst_slow, N_PER_DEC);
    fast_ho_is5_v004(src, src_len, table, dst_fast, N_PER_DEC);
    int correct = (memcmp(dst_slow, dst_fast, N_PER_DEC) == 0);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long d = 0; d < N_DECODES; d++) {
        slow_ho_is5_v004(src, src_len, table, dst_slow, N_PER_DEC);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long d = 0; d < N_DECODES; d++) {
        fast_ho_is5_v004(src, src_len, table, dst_fast, N_PER_DEC);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(table); free(src); free(dst_slow); free(dst_fast);
    return 0;
}
