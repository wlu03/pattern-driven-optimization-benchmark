float slow_sr_1_v040(float *A, float *B, int n, float k0) {
    float total = 0.0f;
    int i = 0;
    while (i < n) {
        total += (k0 - sqrt(A[i])) + sqrt(B[i]);
        i++;
    }
    return total;
}