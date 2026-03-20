double fast_ds4_v005(double *y, int n) {
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += y[i];
    }
    return total_y;
}