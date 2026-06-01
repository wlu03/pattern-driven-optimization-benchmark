static __attribute__((noinline)) double scale_fn_v490(double x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    double r=0;
    for(int k=1;k<=20;k++) r+=(double)sin(_v*k+1.0);
    return r;
}
double fast_comp_v490(double *A, int n, double base, int mode) {
    double s = scale_fn_v490(base);
    double w = (mode == 0) ? s : s * (double)2.0;
    double total = 0;
    for (int i = 0; i < n; i++) total += A[i] * w;
    return total;
}