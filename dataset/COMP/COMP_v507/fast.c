#include <math.h>
static __attribute__((noinline)) float compute_v507(float x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    float r=0;
    for(int k=1;k<=50;k++) r+=(float)sin(_v*k+1.0);
    return r;
}
void fast_comp_v507(float *out, float *A, int n, int key, int mode) {
    float factor = compute_v507(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (float)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (float)1.0;
    }
}