static __attribute__((noinline)) double scale_fn_v113(double base){
    volatile double _b=(double)base; /* block pure/const inference */
    double r = 0;
    for(int k=1;k<=20;k++) r+=(double)sin(_b*k+1.0);
    return r;
}
double slow_comp_v113(double *A, int n, double base, int mode) {
    double total = 0;
    for (int i = 0; i < n; i++) {
        double s = scale_fn_v113(base);
        if (mode == 0) total += A[i] * s;
        else           total += A[i] * s * (double)2.0;
    }
    return total;
}