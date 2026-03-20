double is5_noalias_kernel_v015(double *out, double *A, double *B, int n);
double is5_restrict_kernel_v015(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n);

double fast_is5_v015(double *out, double *A, double *B, int n) {
    int ok = (out + n <= A || A + n <= out) &&
            (out + n <= B || B + n <= out);
    if (ok) return is5_restrict_kernel_v015(out, A, B, n);
    else    return is5_noalias_kernel_v015(out, A, B, n);
}