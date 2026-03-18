#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v006(double *out, double *A, double *B, double *C, int n) {
    int i = 0;
    while (i < n) {
        out[i] = (((A[i] + B[i]) - C[i]) + A[i]) - A[i];
        i++;
    }
}