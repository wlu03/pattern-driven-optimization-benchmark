double fast_ds4_v032(double *amplitude, int n) {
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if (amplitude[i] < total_amplitude) total_amplitude = amplitude[i];
    }
    return total_amplitude;
}