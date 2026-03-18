#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_comp_v003(float *out, float *A, float *B, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                float t1 = A[i*cols+j] + B[i*cols+j];
                float t2 = t1 * (float)2.0;
                float t3 = t2 + (float)1.0;
                float result = t3;
                out[i*cols+j] = result;
            }
        }
    }
}