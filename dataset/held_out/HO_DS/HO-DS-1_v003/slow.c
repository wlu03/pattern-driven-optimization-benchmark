#ifndef HO_DS1_RECORD_DEFINED
#define HO_DS1_RECORD_DEFINED
// 32 doubles = 256 bytes -> 4 cache lines per record.  Hot loop only
// reads hot_a and hot_b (16 bytes); the other 240 bytes per record are
// loaded into cache and never touched.
typedef struct {
    double hot_a;
    double hot_b;
    double cold[30];
} HoDs1Record;
#endif

double aos_sum_ho_ds1_v003(HoDs1Record *recs, int n);

double slow_ho_ds1_v003(HoDs1Record *recs, int n) {
    return aos_sum_ho_ds1_v003(recs, n);
}
