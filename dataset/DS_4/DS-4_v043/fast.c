double fast_ds4_v043(double *timestamp, int n) {
    double total_timestamp = -1e308;
    for (int i = 0; i < n; i++) {
        if (timestamp[i] > total_timestamp) total_timestamp = timestamp[i];
    }
    return total_timestamp;
}