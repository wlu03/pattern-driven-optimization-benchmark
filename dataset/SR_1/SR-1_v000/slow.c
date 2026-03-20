double slow_sr_1_v000(double *A, double *B, double *C, int n, double k0, double k1, double k2) {
    double total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 - A[i]) * (k1 - B[i]) * (k2 - C[i]);
    }
    return total;
}