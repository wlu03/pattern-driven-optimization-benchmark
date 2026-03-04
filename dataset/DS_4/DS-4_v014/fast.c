double fast_ds4_v014(double *id, double *flags, int n) {
    double total_id = 0.0;
    double total_flags = 0.0;
    for (int i = 0; i < n; i++) {
        total_id += id[i];
        total_flags += flags[i];
    }
    return total_id + total_flags;
}