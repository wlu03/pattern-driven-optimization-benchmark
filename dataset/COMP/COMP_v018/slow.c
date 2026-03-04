void slow_comp_v018(double *mat, double *col_avgs, int rows, int cols) {
    // Pattern 1 (MI-4): Column-major traversal
    // Pattern 2 (SR-3): Recompute column sum from scratch for each row prefix
    for (int j = 0; j < cols; j++) {
        double sum = 0.0;
        for (int i = 0; i < rows; i++) {
            sum = 0.0;
            for (int k = 0; k <= i; k++) {
                sum += mat[k * cols + j];  // Column-major access
            }
        }
        col_avgs[j] = sum / rows;
    }
}