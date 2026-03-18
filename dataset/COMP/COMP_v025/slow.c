#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_comp_v025(int *A, int *B, int n, int k, int mode) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        int val;
        if (mode == 1) val = A[i] + B[i] * k;
        else if (mode == 2) val = A[i] - B[i] * k;
        else val = A[i] * B[i] * k;
        total += val;
    }
    return total;
}