double fast_ds4_v007(double *a, double *x, double *y, double *g, int n) {
    double total_a = 0.0;
    double total_x = 0.0;
    double total_y = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_a += a[i];
        total_x += x[i];
        total_y += y[i];
        total_g += g[i];
    }
    return total_a + total_x + total_y + total_g;
}