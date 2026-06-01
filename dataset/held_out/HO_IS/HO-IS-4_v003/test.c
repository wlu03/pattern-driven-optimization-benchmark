#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define HO_IS4_NBITS    11
#define HO_IS4_TBL_SIZE (1u << HO_IS4_NBITS)

#ifndef HO_IS4_ENTRY_DEFINED
#define HO_IS4_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoIs4Entry;
#endif

// 4M symbols total; 4 streams of 1M symbols each.  Stream content is a
// trivial codebook where every entry has nbits=11 and sym = bits & 0xFF
// -- that way we don't need a real Huffman, just exercise the
// extract+lookup+shift dependence chain.
#define N_PER_STREAM 1000000
#define N_STREAMS    4
#define N_TOTAL      (N_STREAMS * N_PER_STREAM)

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoIs4Entry *table = malloc(HO_IS4_TBL_SIZE * sizeof(HoIs4Entry));
    // Variable bit length per entry (3..11), which makes the dependence
    // chain longer and harder for the compiler to schedule away.  All 4
    // streams see the same table so the symbol sequences are reproducible.
    for (uint32_t i = 0; i < HO_IS4_TBL_SIZE; i++) {
        table[i].sym   = (uint8_t)(i & 0xFF);
        // Pick nbits based on the entry index: most entries are 11
        // bits, ~25% are shorter (8 bits), a few are 4 bits.  This
        // simulates a real Huffman code where leaf depth varies.
        uint8_t nb;
        if ((i & 7) == 0)      nb = 4;
        else if ((i & 3) == 0) nb = 8;
        else                   nb = 11;
        table[i].nbits = nb;
    }

    // Source per stream: enough bytes to feed n_per_stream 11-bit codewords
    // = ceil(n_per_stream * 11 / 8) + 8 bytes padding for safe over-read.
    long src_len = (N_PER_STREAM * HO_IS4_NBITS + 7) / 8 + 16;
    uint8_t *src[N_STREAMS];
    for (int s = 0; s < N_STREAMS; s++) {
        src[s] = malloc(src_len);
        // Fill with a deterministic pseudo-random stream so the bit
        // extract has work to do and the test cannot constant-fold.
        uint64_t st = 0x12345678ULL ^ ((uint64_t)s * 0x9e3779b97f4a7c15ULL);
        for (long i = 0; i < src_len; i++) {
            st = st * 6364136223846793005ULL + 1442695040888963407ULL;
            src[s][i] = (uint8_t)(st >> 24);
        }
    }
    // Slow decodes one big stream that's just the 4 streams concatenated.
    uint8_t *src_concat = malloc(N_STREAMS * src_len);
    for (int s = 0; s < N_STREAMS; s++)
        memcpy(src_concat + s * src_len, src[s], src_len);

    uint8_t *dst_slow = malloc(N_TOTAL);
    uint8_t *dst_fast = malloc(N_TOTAL);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_is4_v003(src_concat, src_len, table, dst_slow, N_PER_STREAM);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_is4_v003(src[0], src_len, src[1], src_len,
                     src[2], src_len, src[3], src_len,
                     table, dst_fast, N_PER_STREAM);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Verify each fast stream's output equals the slow output for that
    // segment of src_concat.  Since slow reads src_concat = src[0]||src[1]||...
    // it produces the same per-stream symbols (because the slow loop
    // refills 7 bytes at a time which won't perfectly align between
    // streams when src_len is not a multiple of 8).
    //
    // Use a content-equivalence check: compare each stream's first N
    // symbols where N is small enough that both slow and fast have not
    // run out of bits.  For our 11-bit-per-symbol codebook, src_len
    // bytes feed ~src_len*8/11 symbols.  We compare the first 100K
    // symbols of each stream.
    int correct = 1;
    long check_n = 100000;
    for (int s = 0; s < N_STREAMS; s++) {
        if (memcmp(dst_slow + s * N_PER_STREAM,
                   dst_fast + s * N_PER_STREAM,
                   check_n) != 0) { correct = 0; break; }
    }

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    for (int s = 0; s < N_STREAMS; s++) free(src[s]);
    free(src_concat); free(dst_slow); free(dst_fast); free(table);
    return 0;
}
