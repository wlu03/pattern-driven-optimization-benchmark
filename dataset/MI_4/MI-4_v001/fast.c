void fast_mi4_v001(int *dst, int *src, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            dst[i * cols + j] = src[i * cols + j];
        }
    }
}