double fast_ds4_v011(double *y, double *time, double *amplitude, int n) {
    double total_y = 1e308;
    double total_time = 1e308;
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if (y[i] < total_y) total_y = y[i];
        if (time[i] < total_time) total_time = time[i];
        if (amplitude[i] < total_amplitude) total_amplitude = amplitude[i];
    }
    return total_y + total_time + total_amplitude;
}