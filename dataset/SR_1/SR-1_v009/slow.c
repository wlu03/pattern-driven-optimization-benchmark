float slow_sr_1_v009(float *A, float *B, float *C, float *D, float *E, int rows, int cols, float k0) {
    float total = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + log(A[row * cols + col])) + log(B[row * cols + col]) + log(C[row * cols + col]) + log(D[row * cols + col]) + log(E[row * cols + col]);
        }
    }
    return total;
}