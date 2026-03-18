#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_mi4_v012(int *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] *= (int)3.14;
        }
    }
}