double slow_sr_1_v017(double *A, double *B, double *C, double *D, double *E, double *F, int n, double k0) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += (k0 + A[i]) + B[i] + C[i] + D[i] + E[i] + F[i];
    }
    return total;
}