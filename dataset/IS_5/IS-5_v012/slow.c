float is5_noalias_kernel_v012(float *out, float *A, float *B, int n);

float slow_is5_v012(float *out, float *A, float *B, int n) {
    return is5_noalias_kernel_v012(out, A, B, n);
}