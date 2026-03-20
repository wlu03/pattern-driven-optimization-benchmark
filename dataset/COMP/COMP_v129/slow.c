#include <math.h>
static __attribute__((noinline)) int compute_v129(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    int r=0;
    for(int i=0;i<50;i++) r+=(int)sin(_k+(double)i);
    return r;
}
void slow_comp_v129(int *out, int *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        int factor = compute_v129(key);
        int t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        int t2 = t1 + (int)1.0;
        int t3 = t2;
        out[i] = t3;
    }
}