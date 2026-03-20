double soa_accumulate_ds4_v007(double *pz, double *nw, int n);

double fast_ds4_v007(double *pz, double *nw, int n) {
    return soa_accumulate_ds4_v007(pz, nw, n);
}