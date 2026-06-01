#include <stdint.h>
#include <string.h>

// SLOW: single-stream Huffman-style decoder over a 24-bit codeword
// stream.  Each iteration is a hard chain:
//   1. extract N bits from a 64-bit accumulator
//   2. table-lookup -> (symbol, bit-length)
//   3. emit symbol to output[i]
//   4. shift accumulator down by bit-length
//   5. refill accumulator from input
// Iteration i+1 cannot start step 1 until step 4 of iteration i is
// finished, so per-iter latency is the chain of (load-lookup-add-shift)
// = ~5-7 cycles on modern OoO cores.  ILP is wasted.
//
// Reference: zstd FSE/Huffman decoder (Yann Collet 2015) and Fabian
// Giesen 2023 blog "Reading bits in far too many ways" — the
// canonical single-stream decoder formulation.
#define HO_IS4_NBITS    11                       // 11-bit codewords
#define HO_IS4_TBL_SIZE (1u << HO_IS4_NBITS)

typedef struct { uint8_t sym; uint8_t nbits; } HoIs4Entry;

// Decode one stream (state reset at start) — the natural per-stream loop.
// noinline so the compiler can't fuse + re-interleave the 4 calls.
__attribute__((noinline))
static void slow_ho_is4_decode_stream(const uint8_t *src, long src_len,
                                       const HoIs4Entry *table,
                                       uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *sp = src;
    const uint8_t *send = src + src_len;
    for (long i = 0; i < n_syms; i++) {
        while (bitp <= 56 && sp < send) {
            bits |= ((uint64_t)(*sp++)) << bitp;
            bitp += 8;
        }
        uint32_t k = (uint32_t)(bits & (HO_IS4_TBL_SIZE - 1));
        HoIs4Entry e = table[k];
        dst[i] = e.sym;
        bits >>= e.nbits;
        bitp -= e.nbits;
    }
}

// SLOW: decode 4 streams *sequentially* -- per-stream serial latency
// dominates because each iteration is a hard refill->lookup->shift
// dependence chain (~5-7 cycles).
void slow_ho_is4_v004(const uint8_t *src, long stream_len,
                      const HoIs4Entry *table,
                      uint8_t *dst, long n_per_stream) {
    for (int s = 0; s < 4; s++) {
        slow_ho_is4_decode_stream(src + s * stream_len, stream_len, table,
                                   dst + s * n_per_stream, n_per_stream);
    }
}
