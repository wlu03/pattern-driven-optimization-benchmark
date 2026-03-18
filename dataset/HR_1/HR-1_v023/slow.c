#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v023(int *out, int *A, int *B, int *C, int *D, int n) {
    for (int i = 0; i < n; i++) {
        int temp1 = A[i] * B[i];
        int temp2 = temp1 + C[i];
        int temp3 = temp2 * D[i];
        int temp4 = temp3 + A[i];
        int temp5 = temp4 + B[i];
        int temp6 = temp5 - A[i];
        int result = temp6;
        out[i] = result;
    }
}