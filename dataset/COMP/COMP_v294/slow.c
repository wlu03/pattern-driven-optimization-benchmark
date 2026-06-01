void slow_comp_v294(float *vec, float *mat, float *out, int rows, int cols) {
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            out[j] += vec[i] * mat[i * cols + j];
        }
    }
}