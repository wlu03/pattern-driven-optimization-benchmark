double fast_ds4_v017(double *r, int n) {
    double total_r = 1e308;
    for (int i = 0; i < n; i++) {
        if (r[i] < total_r) total_r = r[i];
    }
    return total_r;
}