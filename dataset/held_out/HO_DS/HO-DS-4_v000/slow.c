#include <stdint.h>

#ifndef HO_DS4_NODE_DEFINED
#define HO_DS4_NODE_DEFINED
// Each Node holds a 16-bit fingerprint (its tag) inside the node itself,
// plus the actual payload.  The bucket-pointer array (HoDs4Node **) just
// holds N raw pointers into a *scattered* pool of nodes.  To check
// whether a bucket might contain a key with fingerprint X, the slow code
// MUST dereference the pointer (DRAM round-trip) to read the tag.
typedef struct {
    uint16_t fp;
    uint16_t _pad;
    int payload;
    char    _padding[248];
} HoDs4Node;
#endif

// Hash-table-bucket "could-contain" probe: for each entry, follow the
// pointer to read the tag (a DRAM load), then on match read the
// payload.  Almost every probe hits DRAM but almost none use the result.
long long check_chain_ho_ds4_v000(HoDs4Node **buckets,
                                    long n, uint16_t want_tag);

long long slow_ho_ds4_v000(HoDs4Node **buckets,
                            long n, uint16_t want_tag) {
    return check_chain_ho_ds4_v000(buckets, n, want_tag);
}
