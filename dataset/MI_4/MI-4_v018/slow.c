#include <math.h>
void slow_mi4_v018(float *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (float)sin((double)matrix[i * cols + j]);
        }
    }
}