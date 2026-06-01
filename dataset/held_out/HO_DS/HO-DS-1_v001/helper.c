#ifndef HO_DS1_RECORD_DEFINED
#define HO_DS1_RECORD_DEFINED
typedef struct {
    double hot_a;
    double hot_b;
    double cold[30];
} HoDs1Record;
#endif

__attribute__((noinline))
double aos_sum_ho_ds1_v001(HoDs1Record *recs, int n) {
    double sa = 0.0, sb = 0.0;
    for (int i = 0; i < n; i++) {
        sa += recs[i].hot_a;
        sb += recs[i].hot_b;
    }
    return sa + sb;
}

__attribute__((noinline))
double soa_sum_ho_ds1_v001(double *hot_a, double *hot_b, int n) {
    double sa = 0.0, sb = 0.0;
    for (int i = 0; i < n; i++) {
        sa += hot_a[i];
        sb += hot_b[i];
    }
    return sa + sb;
}
