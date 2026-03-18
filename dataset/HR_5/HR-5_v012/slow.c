#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr5_v012(double *out, double *A, double *B, int n) {
    int pos = 0;
    for (int i = 0; i < n; i++) {
        double val = A[i] + B[i];
    if (pos < n) {
                out[pos] = val;
                pos++;
    } 
    }
}