float slow_sr_1_v012(float *A, float *B, float *C, float *D, float *E, int n, float k0) {
    float total = 0.0f;
    int i = 0;
    while (i < n) {
        total += (k0 * sqrt(A[i])) + sqrt(B[i]) + sqrt(C[i]) + sqrt(D[i]) + sqrt(E[i]);
        i++;
    }
    return total;
}