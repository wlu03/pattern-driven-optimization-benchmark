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

// SLOW: tag lives inside the (scattered) node, so reading it requires
// a pointer chase to a far-away cache line.  When the pool is large
// enough not to fit in LLC, every probe is a DRAM miss.
__attribute__((noinline))
long long check_chain_ho_ds4_v002(HoDs4Node **buckets,
                                    long n, uint16_t want_tag) {
    long long sum = 0;
    for (long i = 0; i < n; i++) {
        HoDs4Node *node = buckets[i];
        if (node->fp == want_tag) {
            sum += node->payload;
        }
    }
    return sum;
}

// FAST: tag is in the upper 16 bits of the pointer.  No deref on a
// miss.
#define HO_DS4_TAG_SHIFT 48
#define HO_DS4_PTR_MASK  ((uintptr_t)0x0000FFFFFFFFFFFFULL)

__attribute__((noinline))
long long check_packed_ho_ds4_v002(uintptr_t *tagged_buckets,
                                     long n, uint16_t want_tag) {
    long long sum = 0;
    uintptr_t want_hi = (uintptr_t)want_tag << HO_DS4_TAG_SHIFT;
    uintptr_t hi_mask = ~HO_DS4_PTR_MASK;
    for (long i = 0; i < n; i++) {
        uintptr_t tp = tagged_buckets[i];
        if ((tp & hi_mask) == want_hi) {
            HoDs4Node *node = (HoDs4Node *)(tp & HO_DS4_PTR_MASK);
            sum += node->payload;
        }
    }
    return sum;
}
