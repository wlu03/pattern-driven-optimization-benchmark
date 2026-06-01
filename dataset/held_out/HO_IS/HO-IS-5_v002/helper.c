#include <stdint.h>

#ifndef HO_IS5_ENTRY_DEFINED
#define HO_IS5_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoIs5Entry;
#endif

#define HO_IS5_NBITS    11
#define HO_IS5_TBL_SIZE (1u << HO_IS5_NBITS)

// Externally-visible checksum: the real zstd slow path writes a
// running per-symbol checksum / running CRC to a struct field.  We
// model that with an extern volatile to defeat dead-store elimination
// AND register promotion (each write must hit memory).
volatile uint64_t ho_is5_global_chk_v002 = 0;

__attribute__((noinline))
long ho_is5_slow_path_tail_v002(const uint8_t **ipp, uint64_t *bitsp, int *bitpp,
                                 const uint8_t *iend, const HoIs5Entry *table,
                                 uint8_t *dst, long max_emit) {
    const uint8_t *ip = *ipp;
    uint64_t bits = *bitsp;
    int bitp = *bitpp;
    long emitted = 0;
    while (emitted < max_emit) {
        // Defensive byte refill: bytewise loop with per-byte bounds check.
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip) << bitp;
            ip++;
            bitp += 8;
        }
        uint32_t k = (uint32_t)(bits & (HO_IS5_TBL_SIZE - 1));
        HoIs5Entry e = table[k];
        if (e.nbits == 0) break;
        dst[emitted] = e.sym;
        // Per-symbol checksum update -- the volatile load/store forces
        // memory traffic and makes each iteration depend on the
        // previous one.  Models the per-symbol state update that real
        // zstd HUF_decodeStreamX1 performs.
        uint64_t chk = ho_is5_global_chk_v002;
        chk = ((chk + e.sym) * 0x9E3779B97F4A7C15ULL) ^ (chk >> 13);
        ho_is5_global_chk_v002 = chk;
        emitted++;
        bits >>= e.nbits;
        bitp -= e.nbits;
    }
    *ipp = ip; *bitsp = bits; *bitpp = bitp;
    return emitted;
}
