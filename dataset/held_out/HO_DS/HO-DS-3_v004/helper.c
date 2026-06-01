#include <stdint.h>

#ifndef HO_DS3_WIDE_DEFINED
#define HO_DS3_WIDE_DEFINED
typedef struct {
    int64_t level;
    int64_t pad_a;
    int64_t pad_b;
    int64_t pad_c;
    int64_t pad_d;
    int64_t pad_e;
    int64_t pad_f;
    int64_t pad_g;
} HoDs3Wide;
#endif

__attribute__((noinline))
long long sum_wide_ho_ds3_v004(HoDs3Wide *recs, long n) {
    long long s = 0;
    for (long i = 0; i < n; i++) s += recs[i].level;
    return s;
}

__attribute__((noinline))
long long sum_narrow_ho_ds3_v004(uint8_t *levels, long n) {
    long long s = 0;
    for (long i = 0; i < n; i++) s += levels[i];
    return s;
}
