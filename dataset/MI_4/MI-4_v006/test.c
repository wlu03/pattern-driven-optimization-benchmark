#include <stdio.h>
#include <stdlib.h>
#include <math.h>
int slow_mi4_v006(int *matrix, int rows, int cols);
int fast_mi4_v006(int *matrix, int rows, int cols);
int main() {
    int rows = 3000, cols = 1000;
    int *mat = malloc(rows * cols * sizeof(int));
    for (int k = 0; k < rows * cols; k++) mat[k] = (int)(k % 100) * 0.01;
    int s = slow_mi4_v006(mat, rows, cols);
    int f = fast_mi4_v006(mat, rows, cols);
    double diff = fabs((double)(s - f));
    printf("slow=%g fast=%g %s\n", (double)s, (double)f, diff < 1e-2 ? "PASS" : "FAIL");
    free(mat);
    return diff < 1e-2 ? 0 : 1;
}
