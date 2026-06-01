#include <math.h>
static __attribute__((noinline)) int compute_v189(int x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    int r=0;
    for(int k=1;k<=50;k++) r+=(int)sin(_v*k+1.0);
    return r;
}
void fast_comp_v189(int *out, int *A, int n, int key, int mode) {
    int factor = compute_v189(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (int)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (int)1.0;
    }
}