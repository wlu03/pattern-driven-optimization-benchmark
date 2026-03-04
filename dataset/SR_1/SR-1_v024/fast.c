int fast_sr_1_v024(int *A, int *B, int n, int k0, int k1) {
    int sum_A = 0;
    int sum_B = 0;
    int i = 0;
    while (i < n) {
        sum_A += A[i];
        sum_B += B[i];
        i++;
    }
    return (k0 * sum_A) + (k1 * sum_B);
}