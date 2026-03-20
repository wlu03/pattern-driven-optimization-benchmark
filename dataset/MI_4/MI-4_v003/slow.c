#include <math.h>
void slow_mi4_v003(int *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (int)('sqrt', 'math')((double)matrix[i * cols + j]);
        }
    }
}