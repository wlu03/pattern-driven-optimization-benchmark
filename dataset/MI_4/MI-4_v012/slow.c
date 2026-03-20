#include <math.h>
void slow_mi4_v012(double *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (double)('exp', 'math')((double)matrix[i * cols + j]);
        }
    }
}