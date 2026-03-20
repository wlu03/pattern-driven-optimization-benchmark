static __attribute__((noinline)) int log_scale_v126(int base){
    volatile double _b=(double)base; /* block pure/const inference */
    int r = 0;
    for(int k=1;k<=15;k++) r+=(int)(log(_b*k+1.0)/k);
    return r;
}
int fast_comp_v126(int *A, int *B, int rows, int cols, int base) {
    int scale = log_scale_v126(base);
    int sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }
    }
    return scale * sumAsq + scale * sumB;
}