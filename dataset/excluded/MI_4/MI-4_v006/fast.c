#include <math.h>
void fast_mi4_v006(int *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] = (int)cos((double)matrix[i * cols + j]);
        }
    }
}