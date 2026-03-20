double fast_ds4_v013(double *u, int n) {
    double total_u = 0.0;
    int i = 0;
    while (i < n) {
        total_u += u[i];
        i++;
    }
    return total_u;
}