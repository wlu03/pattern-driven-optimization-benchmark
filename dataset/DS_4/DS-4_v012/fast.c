double soa_accumulate_ds4_v012(double *y, double *energy, int n);

double fast_ds4_v012(double *y, double *energy, int n) {
    return soa_accumulate_ds4_v012(y, energy, n);
}