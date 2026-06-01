void fast_comp_v309(float *vec, float *mat, float *out, int rows, int cols) {
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int i = 0; i < rows; i++) {
        float v = vec[i];
        if (v == 0) continue;
        float *row = mat + i * cols;
        for (int j = 0; j < cols; j++) {
            out[j] += v * row[j];
        }
    }
}