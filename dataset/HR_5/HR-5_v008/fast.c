#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr5_v008(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) out[i] = A[i] * B[i];
}