float fast_sr_1_v003(float *A, float *B, float *C, float *D, float *E, int n, float k0, float k1) {
    float sum_A = 1;
    float sum_B = 1;
    float sum_C = 1;
    float sum_D = 1;
    float sum_E = 1;
    for (int i = 0; i < n; i++) {
        sum_A *= (k0 * fabs(A[i]));
        sum_B *= (k1 * fabs(B[i]));
        sum_C *= fabs(C[i]);
        sum_D *= fabs(D[i]);
        sum_E *= fabs(E[i]);
    }
    return sum_A * sum_B * sum_C * sum_D * sum_E;
}