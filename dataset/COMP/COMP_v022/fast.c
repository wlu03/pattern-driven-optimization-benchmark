#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_comp_v022(float *A, float *B, int rows, int cols, float k) {
    float sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }
    }
    return k * sumAsq + k * sumB;
}