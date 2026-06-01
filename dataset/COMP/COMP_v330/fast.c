static __attribute__((noinline)) int scale_fn_v330(int x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    int r=0;
    for(int k=1;k<=20;k++) r+=(int)sin(_v*k+1.0);
    return r;
}
int fast_comp_v330(int *A, int n, int base, int mode) {
    int s = scale_fn_v330(base);
    int w = (mode == 0) ? s : s * (int)2.0;
    int total = 0;
    for (int i = 0; i < n; i++) total += A[i] * w;
    return total;
}