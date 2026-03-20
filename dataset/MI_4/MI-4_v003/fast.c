#include <math.h>
void fast_mi4_v003(int *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] = (int)('sqrt', 'math')((double)matrix[i * cols + j]);
        }
    }
}