float is5_noalias_kernel_v016(float *out, float *A, float *B, int n);
float is5_restrict_kernel_v016(float * __restrict__ out,
        const float * __restrict__ A,
        const float * __restrict__ B, int n);

float fast_is5_v016(float *out, float *A, float *B, int n) {
    int ok = (out + n <= A || A + n <= out) &&
            (out + n <= B || B + n <= out);
    if (ok) return is5_restrict_kernel_v016(out, A, B, n);
    else    return is5_noalias_kernel_v016(out, A, B, n);
}