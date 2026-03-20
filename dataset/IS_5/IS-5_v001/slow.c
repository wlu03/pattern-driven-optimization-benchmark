void is5_noalias_kernel_v001(double *out, double *A, double *B, int n);

void slow_is5_v001(double *out, double *A, double *B, int n) {
    is5_noalias_kernel_v001(out, A, B, n);
}