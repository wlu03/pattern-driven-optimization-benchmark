static __attribute__((noinline)) double log_scale_v079(double base){
    volatile double _b=(double)base; /* block pure/const inference */
    double r = 0;
    for(int k=1;k<=15;k++) r+=(double)(log(_b*k+1.0)/k);
    return r;
}
double slow_comp_v079(double *A, double *B, int rows, int cols, double base) {
    double result = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                double scale = log_scale_v079(base);
                double t1 = A[i*cols+j] * A[i*cols+j];
                double t2 = scale * t1;
                double t3 = B[i*cols+j] * scale;
                result += t2 + t3;
            }
        }
    }
    return result;
}