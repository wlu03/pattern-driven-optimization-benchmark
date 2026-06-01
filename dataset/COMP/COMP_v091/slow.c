static __attribute__((noinline)) double rare_fn_v091(double a){
    volatile double _a=(double)a; /* block ipa-pure-const */
    double r = 0;
    for(int k=1;k<=200;k++) r += (double)sin(_a * k);
    return r;
}
double slow_comp_v091(double *A, double *B, int n) {
    double acc = 0;
    for (int i = 0; i < n; i++) {
        double a = A[i];
        double b = B[i];
        if (a > (double)9) {
            /* rare branch: heavy noinline call per occurrence */
            acc += rare_fn_v091(a);
        } else {
            acc += a * b;
        }
    }
    return acc;
}