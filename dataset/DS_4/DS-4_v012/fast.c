double fast_ds4_v012(double *g, int n) {
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_g += g[i];
    }
    return total_g;
}