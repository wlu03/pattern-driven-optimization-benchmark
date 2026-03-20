double fast_ds4_v003(double *category, double *flags, int n) {
    double total_category = -1e308;
    double total_flags = -1e308;
    int i = 0;
    while (i < n) {
        if (category[i] > total_category) total_category = category[i];
        if (flags[i] > total_flags) total_flags = flags[i];
        i++;
    }
    return total_category + total_flags;
}