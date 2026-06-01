#include <math.h>
static __attribute__((noinline)) int compute_v417(int x){
    volatile double _v=(double)x; /* block ipa-pure-const inference */
    int r=0;
    for(int k=1;k<=50;k++) r+=(int)sin(_v*k+1.0);
    return r;
}
void slow_comp_v417(int *out, int *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        int factor = compute_v417(key);
        int t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        int t2 = t1 + (int)1.0;
        int t3 = t2;
        out[i] = t3;
    }
}