static __attribute__((noinline)) float scale_fn_v047(float base){
    volatile double _b=(double)base; /* block pure/const inference */
    float r = 0;
    for(int k=1;k<=20;k++) r+=(float)sin(_b*k+1.0);
    return r;
}
float slow_comp_v047(float *A, int n, float base, int mode) {
    float total = 0;
    for (int i = 0; i < n; i++) {
        float s = scale_fn_v047(base);
        if (mode == 0) total += A[i] * s;
        else           total += A[i] * s * (float)2.0f;
    }
    return total;
}