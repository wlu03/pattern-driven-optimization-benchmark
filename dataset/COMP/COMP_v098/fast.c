void fast_comp_v098(double *mat, int rows, int cols, int mode) {
    if (mode == 1) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] *= (double)2.0;
    } else if (mode == 2) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] += (double)1.0;
    } else {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] -= (double)0.5;
    }
}