double soa_accumulate_ds4_v011(double *diffuse, double *depth, int n);

double fast_ds4_v011(double *diffuse, double *depth, int n) {
    return soa_accumulate_ds4_v011(diffuse, depth, n);
}