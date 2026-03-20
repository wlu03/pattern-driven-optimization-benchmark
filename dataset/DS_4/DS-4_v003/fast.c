double fast_ds4_v003(double *value, int n) {
    double total_value = 1e308;
    for (int i = 0; i < n; i++) {
        if (value[i] < total_value) total_value = value[i];
    }
    return total_value;
}