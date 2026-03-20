double soa_accumulate_ds4_v004(double *fy, double *potential, int n);

double fast_ds4_v004(double *fy, double *potential, int n) {
    return soa_accumulate_ds4_v004(fy, potential, n);
}