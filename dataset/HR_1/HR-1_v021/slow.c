#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v021(int *out, int *A, int *B, int n) {
    int i = 0;
    while (i < n) {
        int temp1 = A[i] - B[i];
        int temp2 = temp1 + A[i];
        int temp3 = temp2 - B[i];
        int temp4 = temp3 - A[i];
        int result = temp4;
        out[i] = result;
        i++;
    }
}