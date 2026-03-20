#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_mi4_v008(double *out, double *A, double *B, int rows, int cols);
void fast_mi4_v008(double *out, double *A, double *B, int rows, int cols);
int main() {
    int rows = 2000, cols = 2000, total = rows * cols;
    double *A = malloc(total * sizeof(double));
    double *B = malloc(total * sizeof(double));
    double *s = malloc(total * sizeof(double));
    double *f = malloc(total * sizeof(double));
    for (int k = 0; k < total; k++) { A[k] = (double)(k % 100) * 0.1; B[k] = (double)(k % 50) * 0.2; }
    slow_mi4_v008(s, A, B, rows, cols);
    fast_mi4_v008(f, A, B, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-4) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(A); free(B); free(s); free(f);
    return pass ? 0 : 1;
}
