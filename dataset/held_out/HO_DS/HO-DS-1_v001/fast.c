double soa_sum_ho_ds1_v001(double *hot_a, double *hot_b, int n);

double fast_ho_ds1_v001(double *hot_a, double *hot_b, int n) {
    return soa_sum_ho_ds1_v001(hot_a, hot_b, n);
}
