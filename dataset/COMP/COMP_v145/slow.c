void slow_comp_v145(int *out, int *A, int *B, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                int t1 = A[i*cols+j] + B[i*cols+j];
                int t2 = t1 * (int)2.0;
                int t3 = t2 + (int)1.0;
                int result = t3;
                out[i*cols+j] = result;
            }
        }
    }
}