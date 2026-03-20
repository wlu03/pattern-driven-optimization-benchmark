void fast_is1_v002(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        if (B[i] == 0.0) { out[i] = A[i]; continue; }
        out[i] = A[i] - B[i];
    }
}