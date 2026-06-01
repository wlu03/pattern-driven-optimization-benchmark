void fast_comp_v468(int *vec, int *mat, int *out, int rows, int cols) {
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int i = 0; i < rows; i++) {
        int v = vec[i];
        if (v == 0) continue;
        int *row = mat + i * cols;
        for (int j = 0; j < cols; j++) {
            out[j] += v * row[j];
        }
    }
}