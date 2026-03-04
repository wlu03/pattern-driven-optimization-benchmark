float slow_sr_1_v011(float *A, float *B, float *C, float *D, float *E, int n, float k0, float k1, float k2) {
    float total = 0.0f;
    int i = 0;
    while (i < n) {
        total += (k0 + A[i]) + (k1 + B[i]) + (k2 + C[i]) + D[i] + E[i];
        i++;
    }
    return total;
}