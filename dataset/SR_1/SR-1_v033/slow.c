double slow_sr_1_v033(double *A, double *B, double *C, double *D, int n, double k0, double k1, double k2) {
    double total = 0.0;
    int i = 0;
    while (i < n) {
        total += (k0 - A[i]) + (k1 - B[i]) + (k2 - C[i]) + D[i];
        i++;
    }
    return total;
}