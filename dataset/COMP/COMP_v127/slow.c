void slow_comp_v127(int *mat, int rows, int cols, int mode) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            if (mode == 1) mat[i * cols + j] *= (int)2.0;
            else if (mode == 2) mat[i * cols + j] += (int)1.0;
            else mat[i * cols + j] -= (int)0.5;
        }
    }
}