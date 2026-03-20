void fast_comp_v128(double *out, double *A, double *B, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            out[i*cols+j] = (A[i*cols+j] + B[i*cols+j]) * (double)2.0 + (double)1.0;
        }
    }
}