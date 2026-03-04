double fast_ds4_v000(double *flags, double *value, double *weight, int n) {
    double total_flags = 1e308;
    double total_value = 1e308;
    double total_weight = 1e308;
    for (int i = 0; i < n; i++) {
        if (flags[i] < total_flags) total_flags = flags[i];
        if (value[i] < total_value) total_value = value[i];
        if (weight[i] < total_weight) total_weight = weight[i];
    }
    return total_flags + total_value + total_weight;
}