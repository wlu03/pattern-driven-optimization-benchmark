double fast_ds4_v014(double *id, double *timestamp, int n) {
    double total_id = -1e308;
    double total_timestamp = -1e308;
    int i = 0;
    while (i < n) {
        if (id[i] > total_id) total_id = id[i];
        if (timestamp[i] > total_timestamp) total_timestamp = timestamp[i];
        i++;
    }
    return total_id + total_timestamp;
}