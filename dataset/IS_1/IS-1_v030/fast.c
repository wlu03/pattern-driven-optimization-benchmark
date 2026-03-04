float fast_is1_v030(float *A, float *B, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        if (A[i] == 0.0f || B[i] == 0.0f) continue;
        sum += A[i] * B[i];
    }
    return sum;
}