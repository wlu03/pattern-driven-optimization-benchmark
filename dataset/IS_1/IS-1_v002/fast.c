#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is1_v002(float *C, float *a, float *b, int m, int n) {
    for (int i = 0; i < m; i++) {
        if (a[i] == 0.0f) continue;
        for (int j = 0; j < n; j++) {
            if (b[j] == 0.0f) continue;
            C[i * n + j] += a[i] * b[j];
        }
    }
}