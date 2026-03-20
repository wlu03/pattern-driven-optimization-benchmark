void is5_noalias_kernel_v012(float *out, float *A, float *B, int n);

void slow_is5_v012(float *out, float *A, float *B, int n) {
    is5_noalias_kernel_v012(out, A, B, n);
}