double soa_accumulate_ds4_v018(double *normal_y, double *depth, int n);

double fast_ds4_v018(double *normal_y, double *depth, int n) {
    return soa_accumulate_ds4_v018(normal_y, depth, n);
}