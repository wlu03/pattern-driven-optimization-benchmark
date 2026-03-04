double fast_ds4_v045(double *a, double *y, double *normal_x, int n) {
    double total_a = -1e308;
    double total_y = -1e308;
    double total_normal_x = -1e308;
    for (int i = 0; i < n; i++) {
        if (a[i] > total_a) total_a = a[i];
        if (y[i] > total_y) total_y = y[i];
        if (normal_x[i] > total_normal_x) total_normal_x = normal_x[i];
    }
    return total_a + total_y + total_normal_x;
}