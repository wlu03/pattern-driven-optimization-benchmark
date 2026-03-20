double fast_ds4_v006(double *nz, int n) {
    double total_nz = 0.0;
    int i = 0;
    while (i < n) {
        total_nz += nz[i];
        i++;
    }
    return total_nz;
}