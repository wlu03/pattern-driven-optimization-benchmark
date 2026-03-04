void fast_comp_v018(double *mat, double *col_avgs, int rows, int cols) {
    // Fix MI-4: Row-major access order
    // Fix SR-3: Running accumulator instead of recomputation
    for (int j = 0; j < cols; j++) col_avgs[j] = 0.0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            col_avgs[j] += mat[i * cols + j];
        }
    }
    for (int j = 0; j < cols; j++) col_avgs[j] /= rows;
}