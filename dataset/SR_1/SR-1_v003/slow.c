double slow_sr_1_v003(double *A, double *B, int n, double k0) {
    double total = 0.0;
    int i = 0;
    while (i < n) {
        total += (k0 - A[i]) + B[i];
        i++;
    }
    return total;
}