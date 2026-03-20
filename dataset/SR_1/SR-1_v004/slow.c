double slow_sr_1_v004(double *A, double *B, int n, double k0, double k1, double k2, double k3) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += (k0 - log(A[i])) + (k1 - log(B[i]));
    }
    return total;
}