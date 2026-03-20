void is5_noalias_kernel_v010(float *out, float *A, float *B, int n);

void slow_is5_v010(float *out, float *A, float *B, int n) {
    is5_noalias_kernel_v010(out, A, B, n);
}