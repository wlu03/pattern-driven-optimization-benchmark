double soa_accumulate_ds4_v001(double *rate, double *confidence, double *amplitude, int n);

double fast_ds4_v001(double *rate, double *confidence, double *amplitude, int n) {
    return soa_accumulate_ds4_v001(rate, confidence, amplitude, n);
}