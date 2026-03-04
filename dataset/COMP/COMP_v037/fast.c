double fast_comp_v037(double *A, double *B, int n, double k, int mode) {
    double sumA = 0.0, sumB = 0.0;
    // Fix CF-1: Hoist branch
    // Fix SR-1: Factor out invariant k
    if (mode == 1) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA + sumB * k;
    } else if (mode == 2) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA - sumB * k;
    } else {
        double sumAB = 0.0;
        for (int i = 0; i < n; i++) sumAB += A[i] * B[i];
        return sumAB * k;
    }
}