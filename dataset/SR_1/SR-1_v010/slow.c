int slow_sr_1_v010(int *A, int *B, int *C, int *D, int n, int k0, int k1) {
    int total = 0;
    int i = 0;
    while (i < n) {
        total += (k0 + A[i]) + (k1 + B[i]) + C[i] + D[i];
        i++;
    }
    return total;
}