#include <math.h>
__attribute__((noinline))
void fast_mi4_v021(double *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] = (double)fabs((double)matrix[i * cols + j]);
        }
    }
}