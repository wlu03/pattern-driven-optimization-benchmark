double soa_accumulate_ds4_v017(double *ny, double *py, int n);

double fast_ds4_v017(double *ny, double *py, int n) {
    return soa_accumulate_ds4_v017(ny, py, n);
}