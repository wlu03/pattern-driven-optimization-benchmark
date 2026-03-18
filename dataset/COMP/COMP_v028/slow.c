#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float slow_comp_v028(float *A, float *B, int n, float k, int mode) {
    float total = 0;
    for (int i = 0; i < n; i++) {
        float val;
        if (mode == 1) val = A[i] + B[i] * k;
        else if (mode == 2) val = A[i] - B[i] * k;
        else val = A[i] * B[i] * k;
        total += val;
    }
    return total;
}