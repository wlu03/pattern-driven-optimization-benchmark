void slow_mi4_v008(int *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] *= (int)2.0;
        }
    }
}