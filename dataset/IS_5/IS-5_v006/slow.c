void is5_noalias_kernel_v006(double *out, double *A, double *B, int n);

void slow_is5_v006(double *out, double *A, double *B, int n) {
    is5_noalias_kernel_v006(out, A, B, n);
}