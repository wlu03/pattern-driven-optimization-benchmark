#include <math.h>
static __attribute__((noinline)) double compute_v458(double x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    double r=0;
    for(int k=1;k<=50;k++) r+=(double)sin(_v*k+1.0);
    return r;
}
void slow_comp_v458(double *out, double *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        double factor = compute_v458(key);
        double t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        double t2 = t1 + (double)1.0;
        double t3 = t2;
        out[i] = t3;
    }
}