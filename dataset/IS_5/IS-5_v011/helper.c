__attribute__((noinline))
double is5_noalias_kernel_v011(double *out, double *A, double *B, int n) {
    double prev = 0.0;
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*1.5 + B[i]*2.5 - A[i]*B[i]*0.1 + prev * (double)5e-10;
        prev = out[i];
    }
    return prev;
}

__attribute__((noinline))
double is5_restrict_kernel_v011(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*1.5 + B[i]*2.5 - A[i]*B[i]*0.1;
    }
    return out[n > 0 ? n-1 : 0];
}
