double fast_ds4_v008(double *y, double *x, double *b, double *g, int n) {
    double total_y = 0.0;
    double total_x = 0.0;
    double total_b = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += y[i];
        total_x += x[i];
        total_b += b[i];
        total_g += g[i];
    }
    return total_y + total_x + total_b + total_g;
}