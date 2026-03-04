double fast_ds4_v021(double *weight, double *value, double *category, double *flags, int n) {
    double total_weight = 0.0;
    double total_value = 0.0;
    double total_category = 0.0;
    double total_flags = 0.0;
    for (int i = 0; i < n; i++) {
        total_weight += weight[i];
        total_value += value[i];
        total_category += category[i];
        total_flags += flags[i];
    }
    return total_weight + total_value + total_category + total_flags;
}