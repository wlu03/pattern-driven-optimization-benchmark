static __attribute__((noinline)) double scale_fn_v619(double x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    double r=0;
    for(int k=1;k<=20;k++) r+=(double)sin(_v*k+1.0);
    return r;
}
double slow_comp_v619(double *A, int n, double base, int mode) {
    double total = 0;
    for (int i = 0; i < n; i++) {
        double s = scale_fn_v619(base);
        if (mode == 0) total += A[i] * s;
        else           total += A[i] * s * (double)2.0;
    }
    return total;
}