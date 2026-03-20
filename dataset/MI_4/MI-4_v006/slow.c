int slow_mi4_v006(int *matrix, int rows, int cols) {
    int total = 0;
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            total += matrix[i * cols + j];
        }
    }
    return total;
}