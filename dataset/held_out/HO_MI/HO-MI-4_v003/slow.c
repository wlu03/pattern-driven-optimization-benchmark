#include <stdint.h>
#include <string.h>

// SLOW: tight Huffman-style inner loop that RELIES on the compiler to
// auto-unroll the per-symbol body.  Under standard -O3 the compiler
// unrolls this 8x and hits good ILP.  Under security-mitigation flags
// like -mretpoline / -fcf-protection=full / -mcet-switch, the compiler
// becomes conservative about indirect branches and the implicit jump
// targets inserted by unrolling -- and refuses to unroll the body.
// The unrolled-by-compiler version drops to ~30-40% of the bandwidth
// of the manually unrolled version (zstd PR #3826 telemetry).
//
// Reference: zstd PR #3826 (Yann Collet 2023, "Manual unroll for
// Huffman inner loop under CET/retpoline").
#define HO_MI4_NBITS    11
#define HO_MI4_TBL_SIZE (1u << HO_MI4_NBITS)

typedef struct { uint8_t sym; uint8_t nbits; } HoMi4Entry;

extern uint64_t ho_mi4_state_v003;

void slow_ho_mi4_v003(const uint8_t *src, long src_len,
                      const HoMi4Entry *table,
                      uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *ip = src;
    const uint8_t *iend = src + src_len;
    uint64_t state = ho_mi4_state_v003;

    // Tight per-symbol loop -- the compiler is expected to unroll this
    // 8x.  Under retpoline / CET / cf-protection the compiler refuses
    // to unroll (the implicit branch-target cost grows) and the loop
    // runs at one-symbol-per-iter latency.
    for (long i = 0; i < n_syms; i++) {
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip) << bitp;
            ip++;
            bitp += 8;
        }
        HoMi4Entry e = table[bits & (HO_MI4_TBL_SIZE - 1)];
        dst[i] = e.sym;
        // State update: serial dependence chain across iterations --
        // a CRC/checksum analog from the real zstd slow path.
        state = (state ^ e.sym) * 0x100000001b3ULL;
        bits >>= e.nbits;
        bitp -= e.nbits;
    }
    ho_mi4_state_v003 = state;
}
