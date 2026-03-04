double fast_ds4_v015(double *y, int n) {
    double total_y = 1e308;
    int i = 0;
    while (i < n) {
        if (y[i] < total_y) total_y = y[i];
        i++;
    }
    return total_y;
}