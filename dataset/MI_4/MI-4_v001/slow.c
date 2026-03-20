#include <math.h>
void slow_mi4_v001(float *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (float)('sqrt', 'math')((double)matrix[i * cols + j]);
        }
    }
}