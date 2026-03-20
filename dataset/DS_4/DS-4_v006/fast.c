double fast_ds4_v006(double *a, double *b, double *x, int n) {
    double total_a = -1e308;
    double total_b = -1e308;
    double total_x = -1e308;
    int i = 0;
    while (i < n) {
        if (a[i] > total_a) total_a = a[i];
        if (b[i] > total_b) total_b = b[i];
        if (x[i] > total_x) total_x = x[i];
        i++;
    }
    return total_a + total_b + total_x;
}