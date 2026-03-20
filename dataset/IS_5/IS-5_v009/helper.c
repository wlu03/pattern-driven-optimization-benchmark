__attribute__((noinline))
void is5_noalias_kernel_v009(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5f+1.0f;
}

__attribute__((noinline))
void is5_restrict_kernel_v009(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5f+1.0f;
}
