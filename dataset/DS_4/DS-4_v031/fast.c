double fast_ds4_v031(double *quality, double *y, int n) {
    double total_quality = 1e308;
    double total_y = 1e308;
    for (int i = 0; i < n; i++) {
        if (quality[i] < total_quality) total_quality = quality[i];
        if (y[i] < total_y) total_y = y[i];
    }
    return total_quality + total_y;
}