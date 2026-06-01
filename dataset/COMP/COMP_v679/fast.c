void fast_comp_v679(double *vec, double *mat, double *out, int rows, int cols) {
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int i = 0; i < rows; i++) {
        double v = vec[i];
        if (v == 0) continue;
        double *row = mat + i * cols;
        for (int j = 0; j < cols; j++) {
            out[j] += v * row[j];
        }
    }
}