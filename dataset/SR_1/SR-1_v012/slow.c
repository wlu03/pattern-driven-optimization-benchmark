double slow_sr_1_v012(double *A, double *B, int n, double k0) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += (k0 - A[i]) + B[i];
    }
    return total;
}