#include <math.h>
static __attribute__((noinline)) double compute_v039(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    double r=0;
    for(int i=0;i<50;i++) r+=(double)sin(_k+(double)i);
    return r;
}
void fast_comp_v039(double *out, double *A, int n, int key, int mode) {
    double factor = compute_v039(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (double)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (double)1.0;
    }
}