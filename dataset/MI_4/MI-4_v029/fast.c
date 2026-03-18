#include <math.h>
__attribute__((noinline))
void fast_mi4_v029(int *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] = (int)sqrt((double)matrix[i * cols + j]);
        }
    }
}