double fast_ds4_v002(double *value, double *category, double *flags, double *timestamp, int n) {
    double total_value = 0.0;
    double total_category = 0.0;
    double total_flags = 0.0;
    double total_timestamp = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += value[i];
        total_category += category[i];
        total_flags += flags[i];
        total_timestamp += timestamp[i];
    }
    return total_value + total_category + total_flags + total_timestamp;
}