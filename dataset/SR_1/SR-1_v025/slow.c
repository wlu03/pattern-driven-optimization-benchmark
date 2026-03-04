double slow_sr_1_v025(double *A, double *B, double *C, double *D, int n, double k0) {
    double total = 1;
    int i = 0;
    while (i < n) {
        total *= (k0 - A[i]) * B[i] * C[i] * D[i];
        i++;
    }
    return total;
}