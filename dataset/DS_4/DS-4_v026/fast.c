double fast_ds4_v026(double *z, int n) {
    double total_z = 1e308;
    int i = 0;
    while (i < n) {
        if (z[i] < total_z) total_z = z[i];
        i++;
    }
    return total_z;
}