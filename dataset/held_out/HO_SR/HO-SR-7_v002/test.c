#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define HO_SR7_NBITS    11
#define HO_SR7_TBL_SIZE (1u << HO_SR7_NBITS)

#ifndef HO_SR7_ENTRY_DEFINED
#define HO_SR7_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoSr7Entry;
#endif

// Tight inner-loop Huffman decode -- 20M symbols.  The whole loop body
// is dominated by the (extract, lookup, shift) chain; the per-iter
// shift-amount UB guard is on the critical path.
#define N_SYMS 20000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoSr7Entry *table = malloc(HO_SR7_TBL_SIZE * sizeof(HoSr7Entry));
    for (uint32_t i = 0; i < HO_SR7_TBL_SIZE; i++) {
        table[i].sym = (uint8_t)(i & 0xFF);
        uint8_t nb = 11;
        if ((i & 7) == 0)      nb = 4;
        else if ((i & 3) == 0) nb = 8;
        table[i].nbits = nb;
    }
    long src_len = (N_SYMS * HO_SR7_NBITS + 7) / 8 + 64;
    uint8_t *src = malloc(src_len);
    uint64_t st = 0x12345678ULL;
    for (long i = 0; i < src_len; i++) {
        st = st * 6364136223846793005ULL + 1442695040888963407ULL;
        src[i] = (uint8_t)(st >> 24);
    }
    uint8_t *dst_slow = malloc(N_SYMS);
    uint8_t *dst_fast = malloc(N_SYMS);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_sr7_v002(src, src_len, table, dst_slow, N_SYMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_sr7_v002(src, src_len, table, dst_fast, N_SYMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (memcmp(dst_slow, dst_fast, N_SYMS) == 0);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(table); free(src); free(dst_slow); free(dst_fast);
    return 0;
}
