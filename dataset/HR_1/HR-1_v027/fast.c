#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v027(int *out, int *A, int *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = ((A[i] - B[i]) - A[i]) + A[i];
    }
}