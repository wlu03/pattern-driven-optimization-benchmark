#include <math.h>
static __attribute__((noinline)) double compute_v263(double x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    double r=0;
    for(int k=1;k<=50;k++) r+=(double)sin(_v*k+1.0);
    return r;
}
void fast_comp_v263(double *out, double *A, int n, int key, int mode) {
    double factor = compute_v263(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (double)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (double)1.0;
    }
}