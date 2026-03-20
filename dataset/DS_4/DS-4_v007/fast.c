double fast_ds4_v007(double *depth, double *normal_x, int n) {
    double total_depth = -1e308;
    double total_normal_x = -1e308;
    for (int i = 0; i < n; i++) {
        if (depth[i] > total_depth) total_depth = depth[i];
        if (normal_x[i] > total_normal_x) total_normal_x = normal_x[i];
    }
    return total_depth + total_normal_x;
}