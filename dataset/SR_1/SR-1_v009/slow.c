double slow_sr_1_v009(double *A, double *B, double *C, double *D, int n, double k0) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += (k0 + cos(A[i])) + cos(B[i]) + cos(C[i]) + cos(D[i]);
    }
    return total;
}