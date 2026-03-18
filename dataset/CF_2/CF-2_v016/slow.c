#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int cf2_check_v016(int i, int j, int rows, int cols);
void slow_cf2_v016(int *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v016(i, j, rows, cols)) {
                matrix[i * cols + j] *= (int)0.5;
            }
        }
    }
}