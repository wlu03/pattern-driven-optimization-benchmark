float slow_sr_1_v018(float *A, float *B, float *C, float *D, float *E, float *F, int rows, int cols, float k0) {
    float total = 1;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total *= (k0 - A[row * cols + col]) * B[row * cols + col] * C[row * cols + col] * D[row * cols + col] * E[row * cols + col] * F[row * cols + col];
        }
    }
    return total;
}