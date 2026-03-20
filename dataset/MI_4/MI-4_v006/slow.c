#include <math.h>
void slow_mi4_v006(int *matrix, int rows, int cols) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] = (int)cos((double)matrix[i * cols + j]);
        }
    }
}