double soa_accumulate_ds4_v005(double *depth, double *opacity, int n);

double fast_ds4_v005(double *depth, double *opacity, int n) {
    return soa_accumulate_ds4_v005(depth, opacity, n);
}