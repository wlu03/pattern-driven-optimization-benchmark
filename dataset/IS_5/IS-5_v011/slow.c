void is5_noalias_kernel_v011(float *out, float *A, float *B, int n);

void slow_is5_v011(float *out, float *A, float *B, int n) {
    is5_noalias_kernel_v011(out, A, B, n);
}