static __attribute__((noinline)) float scale_fn_v135(float base){
    volatile double _b=(double)base; /* block pure/const inference */
    float r = 0;
    for(int k=1;k<=20;k++) r+=(float)sin(_b*k+1.0);
    return r;
}
float fast_comp_v135(float *A, int n, float base, int mode) {
    float s = scale_fn_v135(base);
    float w = (mode == 0) ? s : s * (float)2.0f;
    float total = 0;
    for (int i = 0; i < n; i++) total += A[i] * w;
    return total;
}