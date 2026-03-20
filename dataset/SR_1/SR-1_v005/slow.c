int slow_sr_1_v005(int *A, int *B, int *C, int *D, int *E, int n, int k0, int k1, int k2, int k3) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += (k0 * A[i]) + (k1 * B[i]) + (k2 * C[i]) + (k3 * D[i]) + E[i];
    }
    return total;
}