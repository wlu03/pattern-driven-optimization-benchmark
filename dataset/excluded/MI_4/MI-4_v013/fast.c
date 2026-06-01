double fast_mi4_v013(double *matrix, int rows, int cols) {
    double total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            total += matrix[i * cols + j];
        }
    }
    return total;
}