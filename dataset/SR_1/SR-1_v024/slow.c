int slow_sr_1_v024(int *A, int *B, int n, int k0, int k1) {
    int total = 0;
    int i = 0;
    while (i < n) {
        total += (k0 * A[i]) + (k1 * B[i]);
        i++;
    }
    return total;
}