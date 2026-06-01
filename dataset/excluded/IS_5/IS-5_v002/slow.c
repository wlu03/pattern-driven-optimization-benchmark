double is5_noalias_kernel_v002(double *out, double *A, double *B, int n);

double slow_is5_v002(double *out, double *A, double *B, int n) {
    return is5_noalias_kernel_v002(out, A, B, n);
}