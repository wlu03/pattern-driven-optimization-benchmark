float slow_sr_1_v016(float *A, float *B, float *C, float *D, float *E, float *F, int rows, int cols, float k0, float k1, float k2) {
    float total = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + sqrt(A[row * cols + col])) + (k1 + sqrt(B[row * cols + col])) + (k2 + sqrt(C[row * cols + col])) + sqrt(D[row * cols + col]) + sqrt(E[row * cols + col]) + sqrt(F[row * cols + col]);
        }
    }
    return total;
}