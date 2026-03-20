#include <math.h>
void fast_mi4_v010(double *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] = (double)fabs((double)matrix[i * cols + j]);
        }
    }
}