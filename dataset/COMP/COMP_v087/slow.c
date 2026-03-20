#include <math.h>
static __attribute__((noinline)) float compute_v087(int key){
    volatile double _k=(double)key; /* block pure/const inference */
    float r=0;
    for(int i=0;i<50;i++) r+=(float)sin(_k+(double)i);
    return r;
}
void slow_comp_v087(float *out, float *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        float factor = compute_v087(key);
        float t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        float t2 = t1 + (float)1.0;
        float t3 = t2;
        out[i] = t3;
    }
}