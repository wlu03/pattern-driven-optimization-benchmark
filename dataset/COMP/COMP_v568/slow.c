static __attribute__((noinline)) int scale_fn_v568(int x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    int r=0;
    for(int k=1;k<=20;k++) r+=(int)sin(_v*k+1.0);
    return r;
}
int slow_comp_v568(int *A, int n, int base, int mode) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        int s = scale_fn_v568(base);
        if (mode == 0) total += A[i] * s;
        else           total += A[i] * s * (int)2.0;
    }
    return total;
}