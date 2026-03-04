int slow_sr_1_v019(int *A, int *B, int *C, int *D, int n, int k0) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += (k0 + A[i]) + B[i] + C[i] + D[i];
    }
    return total;
}