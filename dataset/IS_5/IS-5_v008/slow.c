void is5_noalias_kernel_v008(double *out, double *A, double *B, int n);

void slow_is5_v008(double *out, double *A, double *B, int n) {
    is5_noalias_kernel_v008(out, A, B, n);
}