#include <stdio.h>
#include <stdlib.h>
#include <math.h>
float slow_mi4_v004(float *matrix, int rows, int cols);
float fast_mi4_v004(float *matrix, int rows, int cols);
int main() {
    int rows = 5000, cols = 5000;
    float *mat = malloc(rows * cols * sizeof(float));
    for (int k = 0; k < rows * cols; k++) mat[k] = (float)(k % 100) * 0.01;
    float s = slow_mi4_v004(mat, rows, cols);
    float f = fast_mi4_v004(mat, rows, cols);
    double diff = fabs((double)(s - f));
    printf("slow=%g fast=%g %s\n", (double)s, (double)f, diff < 1e-2 ? "PASS" : "FAIL");
    free(mat);
    return diff < 1e-2 ? 0 : 1;
}
