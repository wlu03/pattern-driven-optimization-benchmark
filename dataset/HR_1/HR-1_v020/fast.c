#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v020(float *out, float *A, float *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = ((A[i] * B[i]) * A[i]) * A[i];
        i++;
    }
}