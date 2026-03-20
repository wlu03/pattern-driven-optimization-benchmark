__attribute__((noinline))
void is5_noalias_kernel_v008(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*1.5+B[i]*2.5-A[i]*B[i]*0.1;
}

__attribute__((noinline))
void is5_restrict_kernel_v008(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*1.5+B[i]*2.5-A[i]*B[i]*0.1;
}
