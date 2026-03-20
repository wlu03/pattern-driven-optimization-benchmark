__attribute__((noinline))
void is5_noalias_kernel_v011(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]+B[i]*2.0f-A[i]*0.5f+B[i]*B[i];
}

__attribute__((noinline))
void is5_restrict_kernel_v011(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]+B[i]*2.0f-A[i]*0.5f+B[i]*B[i];
}
