double fast_ds4_v008(double *g, double *b, double *y, double *normal_x, int n) {
    double total_g = 0.0;
    double total_b = 0.0;
    double total_y = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_g += g[i];
        total_b += b[i];
        total_y += y[i];
        total_normal_x += normal_x[i];
        i++;
    }
    return total_g + total_b + total_y + total_normal_x;
}