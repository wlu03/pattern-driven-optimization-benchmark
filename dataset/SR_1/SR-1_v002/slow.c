double slow_sr_1_v002(double *A, double *B, double *C, double *D, int n, double k0, double k1, double k2, double k3) {
    double total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 - A[i]) * (k1 - B[i]) * (k2 - C[i]) * (k3 - D[i]);
    }
    return total;
}