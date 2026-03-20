void slow_mi4_v013(float *dst, float *src, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            dst[i * cols + j] = src[i * cols + j];
        }
    }
}