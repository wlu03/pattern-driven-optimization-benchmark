double is5_noalias_kernel_v004(double *out, double *A, double *B, int n);

double slow_is5_v004(double *out, double *A, double *B, int n) {
    return is5_noalias_kernel_v004(out, A, B, n);
}