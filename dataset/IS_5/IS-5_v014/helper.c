__attribute__((noinline))
void is5_noalias_kernel_v014(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*1.5f+B[i]*2.5f-A[i]*B[i]*0.1f;
}

__attribute__((noinline))
void is5_restrict_kernel_v014(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*1.5f+B[i]*2.5f-A[i]*B[i]*0.1f;
}
