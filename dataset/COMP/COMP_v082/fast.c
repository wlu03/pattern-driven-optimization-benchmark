#include <math.h>
static __attribute__((noinline)) float compute_v082(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    float r=0;
    for(int i=0;i<50;i++) r+=(float)sin(_k+(double)i);
    return r;
}
void fast_comp_v082(float *out, float *A, int n, int key, int mode) {
    float factor = compute_v082(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (float)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (float)1.0;
    }
}