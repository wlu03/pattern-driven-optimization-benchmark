double slow_sr_1_v030(double *A, double *B, double *C, double *D, double *E, int n, double k0, double k1) {
    double total = 1;
    int i = 0;
    while (i < n) {
        total *= (k0 - A[i]) * (k1 - B[i]) * C[i] * D[i] * E[i];
        i++;
    }
    return total;
}