#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double compute_v015(int key);

void fast_comp_v015(double *out, double *A, int n, int key, int mode) {
    double factor = compute_v015(key);
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + (double)1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + (double)1.0;
    }
}