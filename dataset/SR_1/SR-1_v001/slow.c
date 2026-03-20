int slow_sr_1_v001(int *A, int *B, int *C, int *D, int *E, int n, int k0, int k1, int k2) {
    int total = 0;
    int i = 0;
    while (i < n) {
        total += (k0 - A[i]) + (k1 - B[i]) + (k2 - C[i]) + D[i] + E[i];
        i++;
    }
    return total;
}