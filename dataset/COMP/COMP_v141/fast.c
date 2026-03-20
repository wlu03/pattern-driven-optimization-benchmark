#include <math.h>
static __attribute__((noinline)) int compute_v141(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    int r=0;
    for(int i=0;i<50;i++) r+=(int)sin(_k+(double)i);
    return r;
}
void fast_comp_v141(int *out, int *A, int n, int key, int mode) {
    int factor = compute_v141(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (int)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (int)1.0;
    }
}