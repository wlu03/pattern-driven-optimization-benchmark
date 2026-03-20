double slow_sr_1_v000(double *A, double *B, double *C, double *D, double *E, double *F, int n, double k0) {
    double total = 0.0;
    int i = 0;
    while (i < n) {
        total += (k0 * A[i]) + B[i] + C[i] + D[i] + E[i] + F[i];
        i++;
    }
    return total;
}