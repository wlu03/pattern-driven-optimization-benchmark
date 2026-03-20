static __attribute__((noinline)) float log_scale_v059(float base){
    volatile double _b=(double)base; /* block pure/const inference */
    float r = 0;
    for(int k=1;k<=15;k++) r+=(float)(log(_b*k+1.0)/k);
    return r;
}
float fast_comp_v059(float *A, float *B, int rows, int cols, float base) {
    float scale = log_scale_v059(base);
    float sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }
    }
    return scale * sumAsq + scale * sumB;
}