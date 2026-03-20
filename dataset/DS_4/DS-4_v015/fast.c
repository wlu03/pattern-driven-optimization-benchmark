double soa_accumulate_ds4_v015(double *pm10, double *humidity, double *signal, int n);

double fast_ds4_v015(double *pm10, double *humidity, double *signal, int n) {
    return soa_accumulate_ds4_v015(pm10, humidity, signal, n);
}