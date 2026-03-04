double fast_ds4_v040(double *x, int n) {
    double total_x = 0.0;
    int i = 0;
    while (i < n) {
        total_x += x[i];
        i++;
    }
    return total_x;
}