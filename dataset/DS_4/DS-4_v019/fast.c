double fast_ds4_v019(double *value, double *weight, double *flags, double *id, int n) {
    double total_value = 0.0;
    double total_weight = 0.0;
    double total_flags = 0.0;
    double total_id = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += value[i];
        total_weight += weight[i];
        total_flags += flags[i];
        total_id += id[i];
    }
    return total_value + total_weight + total_flags + total_id;
}