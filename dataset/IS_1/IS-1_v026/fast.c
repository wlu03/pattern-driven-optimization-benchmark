#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is1_v026(float *y, float *x, float alpha, int n) {
    if (alpha == 0.0f) return;
    for (int i = 0; i < n; i++) {
        if (x[i] == 0.0f) continue;
        y[i] += alpha * x[i];
    }
}