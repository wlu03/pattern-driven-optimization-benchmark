double fast_ds4_v004(double *weight, double *flags, double *id, double *timestamp, int n) {
    double total_weight = 0.0;
    double total_flags = 0.0;
    double total_id = 0.0;
    double total_timestamp = 0.0;
    int i = 0;
    while (i < n) {
        total_weight += weight[i];
        total_flags += flags[i];
        total_id += id[i];
        total_timestamp += timestamp[i];
        i++;
    }
    return total_weight + total_flags + total_id + total_timestamp;
}