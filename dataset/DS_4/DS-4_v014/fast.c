double soa_accumulate_ds4_v014(double *amplitude, double *confidence, int n);

double fast_ds4_v014(double *amplitude, double *confidence, int n) {
    return soa_accumulate_ds4_v014(amplitude, confidence, n);
}