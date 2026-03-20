__attribute__((noinline))
float is5_noalias_kernel_v019(float *out, float *A, float *B, int n) {
    float prev = 0.0f;
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*A[i] - B[i]*B[i] + A[i]*B[i]*0.5f + 1.0f + prev * (float)1e-9f;
        prev = out[i];
    }
    return prev;
}

__attribute__((noinline))
float is5_restrict_kernel_v019(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i]*A[i] - B[i]*B[i] + A[i]*B[i]*0.5f + 1.0f;
    }
    return out[n > 0 ? n-1 : 0];
}
