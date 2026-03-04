double fast_ds4_v049(double *normal_x, double *depth, double *x, int n) {
    double total_normal_x = 0.0;
    double total_depth = 0.0;
    double total_x = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_x += normal_x[i];
        total_depth += depth[i];
        total_x += x[i];
        i++;
    }
    return total_normal_x + total_depth + total_x;
}