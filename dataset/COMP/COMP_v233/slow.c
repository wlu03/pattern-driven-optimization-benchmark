static __attribute__((noinline)) int rare_fn_v233(int a){
    volatile double _a=(double)a; /* block ipa-pure-const */
    int r = 0;
    for(int k=1;k<=200;k++) r += (int)sin(_a * k);
    return r;
}
int slow_comp_v233(int *A, int *B, int n) {
    int acc = 0;
    for (int i = 0; i < n; i++) {
        int a = A[i];
        int b = B[i];
        if (a > (int)9) {
            /* rare branch: heavy noinline call per occurrence */
            acc += rare_fn_v233(a);
        } else {
            acc += a * b;
        }
    }
    return acc;
}