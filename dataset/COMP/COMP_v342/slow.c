#include <math.h>
static __attribute__((noinline)) float compute_v342(float x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    float r=0;
    for(int k=1;k<=50;k++) r+=(float)sin(_v*k+1.0);
    return r;
}
void slow_comp_v342(float *out, float *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        float factor = compute_v342(key);
        float t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        float t2 = t1 + (float)1.0;
        float t3 = t2;
        out[i] = t3;
    }
}