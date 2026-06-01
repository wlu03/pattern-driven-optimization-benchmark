void slow_comp_v468(int *vec, int *mat, int *out, int rows, int cols) {
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            out[j] += vec[i] * mat[i * cols + j];
        }
    }
}