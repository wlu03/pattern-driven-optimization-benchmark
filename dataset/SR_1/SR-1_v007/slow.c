int slow_sr_1_v007(int *A, int *B, int *C, int *D, int *E, int n, int k0, int k1) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += (k0 + A[i]) + (k1 + B[i]) + C[i] + D[i] + E[i];
    }
    return total;
}