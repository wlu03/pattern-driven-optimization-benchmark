void is5_noalias_kernel_v014(float *out, float *A, float *B, int n);

void slow_is5_v014(float *out, float *A, float *B, int n) {
    is5_noalias_kernel_v014(out, A, B, n);
}