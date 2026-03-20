void slow_comp_v010(double *out, double *A, double *B, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                double t1 = A[i*cols+j] + B[i*cols+j];
                double t2 = t1 * (double)2.0;
                double t3 = t2 + (double)1.0;
                double result = t3;
                out[i*cols+j] = result;
            }
        }
    }
}