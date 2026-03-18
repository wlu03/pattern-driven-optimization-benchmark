#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float compute_v025(int key);

void slow_comp_v025(float *out, float *A, int n, int key, int mode) {
    for (int i = 0; i < n; i++) {
        float factor = compute_v025(key);
        float t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        float t2 = t1 + (float)1.0;
        float t3 = t2;
        out[i] = t3;
    }
}