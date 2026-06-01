#include <stdint.h>

#ifndef HO_DS4_NODE_DEFINED
#define HO_DS4_NODE_DEFINED
typedef struct {
    uint16_t fp;
    uint16_t _pad;
    int payload;
    char    _padding[248];
} HoDs4Node;
#endif

// FAST: pack the 16-bit fingerprint into the upper 16 bits of the
// bucket pointer.  Now the could-contain check uses ONLY the
// already-loaded pointer word — no DRAM round-trip to a scattered node.
// Only on a tag match do we mask off the upper bits, materialize the
// real pointer, and pay for the node fetch.  When most probes miss
// (the common Bloom-filter regime), this turns N DRAM hits into ~0.
//
// Cite: Birler/Schmidt/Fent/Neumann CedarDB DaMoN'24 hash-table paper.
// Caveat: Intel 5-level paging (Ice Lake+) reduces usable upper bits
// from 16 to 7 — pattern still applies, choose a narrower tag.
long long check_packed_ho_ds4_v003(uintptr_t *tagged_buckets,
                                     long n, uint16_t want_tag);

long long fast_ho_ds4_v003(uintptr_t *tagged_buckets,
                            long n, uint16_t want_tag) {
    return check_packed_ho_ds4_v003(tagged_buckets, n, want_tag);
}
