double fast_ds4_v010(double *r, double *b, int n) {
    double total_r = 1e308;
    double total_b = 1e308;
    for (int i = 0; i < n; i++) {
        if (r[i] < total_r) total_r = r[i];
        if (b[i] < total_b) total_b = b[i];
    }
    return total_r + total_b;
}