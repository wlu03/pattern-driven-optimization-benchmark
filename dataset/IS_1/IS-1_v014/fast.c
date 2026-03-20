void fast_is1_v014(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) {
        if (B[i] == 0.0f) { out[i] = A[i]; continue; }
        out[i] = A[i] - B[i];
    }
}