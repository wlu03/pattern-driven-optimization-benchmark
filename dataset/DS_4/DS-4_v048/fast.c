double fast_ds4_v048(double *y, double *x, double *vy, int n) {
    double total_y = -1e308;
    double total_x = -1e308;
    double total_vy = -1e308;
    for (int i = 0; i < n; i++) {
        if (y[i] > total_y) total_y = y[i];
        if (x[i] > total_x) total_x = x[i];
        if (vy[i] > total_vy) total_vy = vy[i];
    }
    return total_y + total_x + total_vy;
}