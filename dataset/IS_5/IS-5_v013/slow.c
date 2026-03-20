float is5_noalias_kernel_v013(float *out, float *A, float *B, int n);

float slow_is5_v013(float *out, float *A, float *B, int n) {
    return is5_noalias_kernel_v013(out, A, B, n);
}