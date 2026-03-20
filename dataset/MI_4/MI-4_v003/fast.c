void fast_mi4_v003(double *dst, double *src, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            dst[i * cols + j] = src[i * cols + j];
        }
    }
}