double fast_ds4_v002(double *y, int n) {
    double total_y = 1e308;
    for (int i = 0; i < n; i++) {
        if (y[i] < total_y) total_y = y[i];
    }
    return total_y;
}