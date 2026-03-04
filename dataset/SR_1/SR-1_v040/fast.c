float fast_sr_1_v040(float *A, float *B, int n, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    int i = 0;
    while (i < n) {
        sum_A += sqrt(A[i]);
        sum_B += sqrt(B[i]);
        i++;
    }
    return (k0 - sum_A) + sum_B;
}