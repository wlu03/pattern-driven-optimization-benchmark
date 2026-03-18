#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int hr5_check_v006(double val);
void slow_hr5_v006(double *out, double *A, double *B, int n) {
    int pos = 0;
    for (int i = 0; i < n; i++) {
        double val = A[i] * B[i];
        if (hr5_check_v006(val)) {
            out[pos++] = val;
        }
    }
}