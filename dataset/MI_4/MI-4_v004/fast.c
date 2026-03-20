float fast_mi4_v004(float *matrix, int rows, int cols) {
    float total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            total += matrix[i * cols + j];
        }
    }
    return total;
}