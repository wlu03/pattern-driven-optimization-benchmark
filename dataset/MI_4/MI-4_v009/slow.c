double slow_mi4_v009(double *matrix, int rows, int cols) {
    double total = 0;
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            total += matrix[i * cols + j];
        }
    }
    return total;
}