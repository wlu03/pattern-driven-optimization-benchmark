#include <math.h>
void slow_mi4_v012(int *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (int)log((double)matrix[i * cols + j]);
        }
    }
}