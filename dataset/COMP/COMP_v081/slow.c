void slow_comp_v081(float *mat, float *col_avgs, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        float sum = 0;
        for (int i = 0; i < rows; i++) {
            sum = 0;
            for (int k = 0; k <= i; k++) {
                sum += mat[k * cols + j];
            }
        }
        col_avgs[j] = sum / (float)rows;
    }
}