#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v016(int *out, int *A, int *B, int n) {
    int i = 0;
    while (i < n) {
        int temp1 = A[i] - B[i];
        int temp2 = temp1 + A[i];
        int result = temp2;
        out[i] = result;
        i++;
    }
}