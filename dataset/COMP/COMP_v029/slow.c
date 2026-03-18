#include <math.h>
__attribute__((noinline))
int compute_v029(int key);

void slow_comp_v029(int *out, int *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        int factor = compute_v029(key);
        int t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        int t2 = t1 + (int)1.0;
        int t3 = t2;
        out[i] = t3;
    }
}
int compute_v029(int key) {
    int r = 0;
    for (int i = 0; i < 50; i++) r += (int)sin((double)(key+i));
    return r;
}