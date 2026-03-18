#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float compute_v016(int key);

void fast_comp_v016(float *out, float *A, int n, int key, int mode) {
    float factor = compute_v016(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (float)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (float)1.0;
    }
}