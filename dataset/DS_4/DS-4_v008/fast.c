double fast_ds4_v008(double *quality, int n) {
    double total_quality = 0.0;
    for (int i = 0; i < n; i++) {
        total_quality += quality[i];
    }
    return total_quality;
}