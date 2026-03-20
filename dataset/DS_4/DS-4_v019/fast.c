double soa_accumulate_ds4_v019(double *y, double *g, int n);

double fast_ds4_v019(double *y, double *g, int n) {
    return soa_accumulate_ds4_v019(y, g, n);
}