static __attribute__((noinline)) float rare_fn_v408(float a){
    volatile double _a=(double)a; /* block ipa-pure-const */
    float r = 0;
    for(int k=1;k<=200;k++) r += (float)sin(_a * k);
    return r;
}
float slow_comp_v408(float *A, float *B, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        float a = A[i];
        float b = B[i];
        if (a > (float)9) {
            /* rare branch: heavy noinline call per occurrence */
            acc += rare_fn_v408(a);
        } else {
            acc += a * b;
        }
    }
    return acc;
}