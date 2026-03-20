#include <stdio.h>
#include <stdlib.h>
#include <math.h>
double slow_mi4_v007(double *matrix, int rows, int cols);
double fast_mi4_v007(double *matrix, int rows, int cols);
int main() {
    int rows = 2000, cols = 1000;
    double *mat = malloc(rows * cols * sizeof(double));
    for (int k = 0; k < rows * cols; k++) mat[k] = (double)(k % 100) * 0.01;
    double s = slow_mi4_v007(mat, rows, cols);
    double f = fast_mi4_v007(mat, rows, cols);
    double diff = fabs((double)(s - f));
    printf("slow=%g fast=%g %s\n", (double)s, (double)f, diff < 1e-2 ? "PASS" : "FAIL");
    free(mat);
    return diff < 1e-2 ? 0 : 1;
}
