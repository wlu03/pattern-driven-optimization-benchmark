__attribute__((noinline))
double is5_noalias_kernel_v007(double *out, double *A, double *B, int n) {
    double prev = 0.0;
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*A[i] + B[i]*2.0 - A[i]*0.5 + B[i]*B[i] + prev * (double)1e-9;
        prev = out[i];
    }
    return prev;
}

__attribute__((noinline))
double is5_restrict_kernel_v007(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*A[i] + B[i]*2.0 - A[i]*0.5 + B[i]*B[i];
    }
    return out[n > 0 ? n-1 : 0];
}
