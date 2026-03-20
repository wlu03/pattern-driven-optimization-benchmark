double fast_ds4_v007(double *vy, double *y, int n) {
    double total_vy = 0.0;
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_vy += vy[i];
        total_y += y[i];
    }
    return total_vy + total_y;
}