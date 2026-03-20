double fast_ds4_v014(double *timestamp, int n) {
    double total_timestamp = -1e308;
    int i = 0;
    while (i < n) {
        if (timestamp[i] > total_timestamp) total_timestamp = timestamp[i];
        i++;
    }
    return total_timestamp;
}