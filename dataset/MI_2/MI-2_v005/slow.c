#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_mi2_v005(int *output, int *A, int *B, int n) {
    memset(output, 0, n * sizeof(int));
    for (int i = 0; i < n; i++) output[i] = A[i] * A[i] + B[i];
}