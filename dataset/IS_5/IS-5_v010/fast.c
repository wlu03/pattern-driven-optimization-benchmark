void is5_noalias_kernel_v010(float *out, float *A, float *B, int n);
void is5_restrict_kernel_v010(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n);

void fast_is5_v010(float *out, float *A, float *B, int n) {
    int ok = (out + n <= A || A + n <= out) &&
            (out + n <= B || B + n <= out);
    if (ok) is5_restrict_kernel_v010(out, A, B, n);
    else    is5_noalias_kernel_v010(out, A, B, n);
}