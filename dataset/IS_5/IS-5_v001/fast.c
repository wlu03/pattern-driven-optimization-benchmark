void is5_noalias_kernel_v001(double *out, double *A, double *B, int n);
void is5_restrict_kernel_v001(double * __restrict__ out,
        const double * __restrict__ A,
        const double * __restrict__ B, int n);

void fast_is5_v001(double *out, double *A, double *B, int n) {
    int ok = (out + n <= A || A + n <= out) &&
            (out + n <= B || B + n <= out);
    if (ok) is5_restrict_kernel_v001(out, A, B, n);
    else    is5_noalias_kernel_v001(out, A, B, n);
}