__attribute__((noinline))
void is5_noalias_kernel_v013(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5+1.0;
}

__attribute__((noinline))
void is5_restrict_kernel_v013(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5+1.0;
}
