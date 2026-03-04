int slow_sr_1_v041(int *A, int *B, int *C, int *D, int *E, int n, int k0) {
    int total = 0;
    int i = 0;
    while (i < n) {
        total += (k0 - A[i]) + B[i] + C[i] + D[i] + E[i];
        i++;
    }
    return total;
}