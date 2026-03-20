double soa_accumulate_ds4_v003(double *temp, double *co2, double *signal, int n);

double fast_ds4_v003(double *temp, double *co2, double *signal, int n) {
    return soa_accumulate_ds4_v003(temp, co2, signal, n);
}