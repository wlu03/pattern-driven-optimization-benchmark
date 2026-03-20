void is5_noalias_kernel_v005(float *out, float *A, float *B, int n);

void slow_is5_v005(float *out, float *A, float *B, int n) {
    is5_noalias_kernel_v005(out, A, B, n);
}