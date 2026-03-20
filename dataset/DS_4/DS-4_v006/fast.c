double fast_ds4_v006(double *x, double *quality, int n) {
    double total_x = 1e308;
    double total_quality = 1e308;
    for (int i = 0; i < n; i++) {
        if (x[i] < total_x) total_x = x[i];
        if (quality[i] < total_quality) total_quality = quality[i];
    }
    return total_x + total_quality;
}