#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v022(int *out, int *A, int *B, int *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = (((((A[i] + B[i]) + C[i]) * A[i]) * B[i]) - C[i]) + A[i];
    }
}