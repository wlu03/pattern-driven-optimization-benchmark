#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_mi4_v001(int *out, int *A, int *B, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            out[i * cols + j] = A[i * cols + j] + B[i * cols + j];
        }
    }
}