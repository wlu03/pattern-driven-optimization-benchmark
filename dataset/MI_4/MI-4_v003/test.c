#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_mi4_v003(double *dst, double *src, int rows, int cols);
void fast_mi4_v003(double *dst, double *src, int rows, int cols);
int main() {
    int rows = 2000, cols = 1000, total = rows * cols;
    double *src = malloc(total * sizeof(double));
    double *s = malloc(total * sizeof(double));
    double *f = malloc(total * sizeof(double));
    for (int k = 0; k < total; k++) src[k] = (double)(k % 100) * 0.1;
    slow_mi4_v003(s, src, rows, cols);
    fast_mi4_v003(f, src, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-9) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(src); free(s); free(f);
    return pass ? 0 : 1;
}
