#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v001(int *out, int *A, int *B, int *C, int *D, int n) {
    int i = 0;
    while (i < n) {
        out[i] = ((A[i] + B[i]) + C[i]) + A[i];
        i++;
    }
}