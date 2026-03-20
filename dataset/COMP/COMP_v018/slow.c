void slow_comp_v018(double *mat, double *col_avgs, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        double sum = 0;
        for (int i = 0; i < rows; i++) {
            sum = 0;
            for (int k = 0; k <= i; k++) {
                sum += mat[k * cols + j];
            }
        }
        col_avgs[j] = sum / (double)rows;
    }
}