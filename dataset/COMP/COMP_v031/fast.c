void fast_comp_v031(int *out, int *A, int *B, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            out[i*cols+j] = (A[i*cols+j] + B[i*cols+j]) * (int)2.0 + (int)1.0;
        }
    }
}