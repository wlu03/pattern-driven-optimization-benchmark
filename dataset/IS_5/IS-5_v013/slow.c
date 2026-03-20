void is5_noalias_kernel_v013(double *out, double *A, double *B, int n);

void slow_is5_v013(double *out, double *A, double *B, int n) {
    is5_noalias_kernel_v013(out, A, B, n);
}