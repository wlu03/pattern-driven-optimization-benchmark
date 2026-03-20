#include <math.h>
static __attribute__((noinline)) double compute_v092(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    double r=0;
    for(int i=0;i<50;i++) r+=(double)sin(_k+(double)i);
    return r;
}
void slow_comp_v092(double *out, double *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        double factor = compute_v092(key);
        double t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        double t2 = t1 + (double)1.0;
        double t3 = t2;
        out[i] = t3;
    }
}