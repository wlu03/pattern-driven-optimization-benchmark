double fast_ds4_v042(double *y, double *a, int n) {
    double total_y = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += y[i];
        total_a += a[i];
    }
    return total_y + total_a;
}