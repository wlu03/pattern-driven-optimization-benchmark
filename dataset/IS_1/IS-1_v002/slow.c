void slow_is1_v002(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] + B[i];
    }
}