void fast_is1_v045(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) {
        if (A[i] == 0.0f || B[i] == 0.0f) {
            out[i] = 0.0f;
            continue;
        }
        out[i] = A[i] * B[i];
    }
}