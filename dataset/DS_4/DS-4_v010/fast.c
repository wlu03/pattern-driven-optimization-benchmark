double fast_ds4_v010(double *ny, int n) {
    double total_ny = -1e308;
    int i = 0;
    while (i < n) {
        if (ny[i] > total_ny) total_ny = ny[i];
        i++;
    }
    return total_ny;
}