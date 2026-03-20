void fast_comp_v127(int *mat, int rows, int cols, int mode) {
    if (mode == 1) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] *= (int)2.0;
    } else if (mode == 2) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] += (int)1.0;
    } else {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] -= (int)0.5;
    }
}