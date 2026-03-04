double slow_sr_1_v031(double *A, double *B, int n, double k0, double k1, double k2) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += (k0 - A[i]) + (k1 - B[i]);
    }
    return total;
}