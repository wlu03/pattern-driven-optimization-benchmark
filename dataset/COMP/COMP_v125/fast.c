void fast_comp_v125(float *mat, int rows, int cols, int mode) {
    if (mode == 1) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] *= (float)2.0;
    } else if (mode == 2) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] += (float)1.0;
    } else {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] -= (float)0.5;
    }
}