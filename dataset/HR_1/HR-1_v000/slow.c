#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v000(int *out, int *A, int *B, int n) {
    for (int i = 0; i < n; i++) {
        int temp1 = A[i] - B[i];
        int temp2 = temp1 + A[i];
        int temp3 = temp2 + B[i];
        int temp4 = temp3 + A[i];
        int temp5 = temp4 - A[i];
        int result = temp5;
        out[i] = result;
    }
}