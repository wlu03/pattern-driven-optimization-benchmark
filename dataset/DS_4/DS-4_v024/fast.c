double fast_ds4_v024(double *y, double *amplitude, double *channel, int n) {
    double total_y = -1e308;
    double total_amplitude = -1e308;
    double total_channel = -1e308;
    for (int i = 0; i < n; i++) {
        if (y[i] > total_y) total_y = y[i];
        if (amplitude[i] > total_amplitude) total_amplitude = amplitude[i];
        if (channel[i] > total_channel) total_channel = channel[i];
    }
    return total_y + total_amplitude + total_channel;
}