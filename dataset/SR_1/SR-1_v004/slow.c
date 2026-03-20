float slow_sr_1_v004(float *A, float *B, float *C, float *D, float *E, int n, float k0) {
    float total = 0.0f;
    int i = 0;
    while (i < n) {
        total += (k0 - A[i]) + B[i] + C[i] + D[i] + E[i];
        i++;
    }
    return total;
}