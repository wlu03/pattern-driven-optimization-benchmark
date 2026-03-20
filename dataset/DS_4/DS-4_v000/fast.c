double soa_accumulate_ds4_v000(double *pressure, double *ozone, int n);

double fast_ds4_v000(double *pressure, double *ozone, int n) {
    return soa_accumulate_ds4_v000(pressure, ozone, n);
}