static __attribute__((noinline)) double log_scale_v110(double base){
    volatile double _b=(double)base; /* block pure/const inference */
    double r = 0;
    for(int k=1;k<=15;k++) r+=(double)(log(_b*k+1.0)/k);
    return r;
}
double fast_comp_v110(double *A, double *B, int rows, int cols, double base) {
    double scale = log_scale_v110(base);
    double sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }
    }
    return scale * sumAsq + scale * sumB;
}