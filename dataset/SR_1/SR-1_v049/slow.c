float slow_sr_1_v049(float *A, float *B, float *C, float *D, int n, float k0) {
    float total = 1;
    int i = 0;
    while (i < n) {
        total *= (k0 * A[i]) * B[i] * C[i] * D[i];
        i++;
    }
    return total;
}