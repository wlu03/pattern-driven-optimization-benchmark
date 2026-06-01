#ifndef HO_DS3_WIDE_DEFINED
#define HO_DS3_WIDE_DEFINED
// 64-byte (1 cache line per record) struct.  The `level` field is declared
// `int64_t` even though it only ever stores values in [0, 255] (e.g. a log
// level, a small enum tag, etc.).  Abseil Tip #62 calls this out: integers
// over a small range fit in int8_t but are routinely declared as int64_t.
// At n=1e6 records, this loop is bandwidth-bound: 64 MB of memory traffic
// to read a single field per record.
#include <stdint.h>
typedef struct {
    int64_t level;     // actual range [0,255], wastes 7 bytes of cache
    int64_t pad_a;
    int64_t pad_b;
    int64_t pad_c;
    int64_t pad_d;
    int64_t pad_e;
    int64_t pad_f;
    int64_t pad_g;
} HoDs3Wide;
#endif

long long sum_wide_ho_ds3_v002(HoDs3Wide *recs, long n);

long long slow_ho_ds3_v002(HoDs3Wide *recs, long n) {
    return sum_wide_ho_ds3_v002(recs, n);
}
