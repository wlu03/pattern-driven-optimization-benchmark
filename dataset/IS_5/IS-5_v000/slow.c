double is5_noalias_kernel_v000(double *out, double *A, double *B, int n);

double slow_is5_v000(double *out, double *A, double *B, int n) {
    return is5_noalias_kernel_v000(out, A, B, n);
}