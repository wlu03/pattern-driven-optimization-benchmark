__attribute__((noinline))
float is5_noalias_kernel_v016(float *out, float *A, float *B, int n) {
    float prev = 0.0f;
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*1.5f + B[i]*2.5f - A[i]*B[i]*0.1f + prev * (float)2e-9f;
        prev = out[i];
    }
    return prev;
}

__attribute__((noinline))
float is5_restrict_kernel_v016(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*1.5f + B[i]*2.5f - A[i]*B[i]*0.1f;
    }
    return out[n > 0 ? n-1 : 0];
}
