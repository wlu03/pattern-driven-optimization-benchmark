float is5_noalias_kernel_v001(float *out, float *A, float *B, int n);

float slow_is5_v001(float *out, float *A, float *B, int n) {
    return is5_noalias_kernel_v001(out, A, B, n);
}