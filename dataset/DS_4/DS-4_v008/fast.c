double soa_accumulate_ds4_v008(double *radiation, double *humidity, double *signal, int n);

double fast_ds4_v008(double *radiation, double *humidity, double *signal, int n) {
    return soa_accumulate_ds4_v008(radiation, humidity, signal, n);
}