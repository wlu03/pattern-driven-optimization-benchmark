double fast_ds4_v013(double *b, double *g, double *normal_x, int n) {
    double total_b = 0.0;
    double total_g = 0.0;
    double total_normal_x = 0.0;
    for (int i = 0; i < n; i++) {
        total_b += b[i];
        total_g += g[i];
        total_normal_x += normal_x[i];
    }
    return total_b + total_g + total_normal_x;
}