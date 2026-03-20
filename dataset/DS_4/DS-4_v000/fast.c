double fast_ds4_v000(double *g, double *r, double *x, int n) {
    double total_g = 1e308;
    double total_r = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if (g[i] < total_g) total_g = g[i];
        if (r[i] < total_r) total_r = r[i];
        if (x[i] < total_x) total_x = x[i];
    }
    return total_g + total_r + total_x;
}