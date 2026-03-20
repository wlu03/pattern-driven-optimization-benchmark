void fast_is1_v000(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        if (A[i] == 0.0 || B[i] == 0.0) {
            out[i] = 0.0;
            continue;
        }
        out[i] = A[i] * B[i];
    }
}