#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int compute_v007(int key);

void fast_comp_v007(int *out, int *A, int n, int key, int mode) {
    int factor = compute_v007(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (int)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (int)1.0;
    }
}