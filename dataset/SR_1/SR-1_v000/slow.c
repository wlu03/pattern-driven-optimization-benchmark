double slow_sr_1_v000(double *A, double *B, double *C, double *D, double *E, double *F, int n, double k0, double k1, double k2) {
    double total = 1;
    int i = 0;
    while (i < n) {
        total *= (k0 * A[i]) * (k1 * B[i]) * (k2 * C[i]) * D[i] * E[i] * F[i];
        i++;
    }
    return total;
}