static __attribute__((noinline)) int log_scale_v073(int base){
    volatile double _b=(double)base; /* block pure/const inference */
    int r = 0;
    for(int k=1;k<=15;k++) r+=(int)(log(_b*k+1.0)/k);
    return r;
}
int slow_comp_v073(int *A, int *B, int rows, int cols, int base) {
    int result = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                int scale = log_scale_v073(base);
                int t1 = A[i*cols+j] * A[i*cols+j];
                int t2 = scale * t1;
                int t3 = B[i*cols+j] * scale;
                result += t2 + t3;
            }
        }
    }
    return result;
}