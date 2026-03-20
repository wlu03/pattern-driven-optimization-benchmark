static __attribute__((noinline)) float log_scale_v074(float base){
    volatile double _b=(double)base; /* block pure/const inference */
    float r = 0;
    for(int k=1;k<=15;k++) r+=(float)(log(_b*k+1.0)/k);
    return r;
}
float slow_comp_v074(float *A, float *B, int rows, int cols, float base) {
    float result = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                float scale = log_scale_v074(base);
                float t1 = A[i*cols+j] * A[i*cols+j];
                float t2 = scale * t1;
                float t3 = B[i*cols+j] * scale;
                result += t2 + t3;
            }
        }
    }
    return result;
}