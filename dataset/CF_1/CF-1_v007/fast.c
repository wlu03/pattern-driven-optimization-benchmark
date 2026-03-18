#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf1_v007(int *out, int *A, int *B, int *C, int n, int mode) {
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = (A[i] + B[i]) - C[i];
    } else if (mode == 2) {
        for (int i = 0; i < n; i++) out[i] = (A[i] - B[i]) + C[i];
    } else if (mode == 3) {
        for (int i = 0; i < n; i++) out[i] = (A[i] * B[i]) + C[i];
    } else {
        for (int i = 0; i < n; i++) out[i] = (A[i] - B[i]) - C[i];
    }
}