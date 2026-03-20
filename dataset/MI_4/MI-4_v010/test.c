#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_mi4_v010(float *out, float *A, float *B, int rows, int cols);
void fast_mi4_v010(float *out, float *A, float *B, int rows, int cols);
int main() {
    int rows = 4000, cols = 4000, total = rows * cols;
    float *A = malloc(total * sizeof(float));
    float *B = malloc(total * sizeof(float));
    float *s = malloc(total * sizeof(float));
    float *f = malloc(total * sizeof(float));
    for (int k = 0; k < total; k++) { A[k] = (float)(k % 100) * 0.1; B[k] = (float)(k % 50) * 0.2; }
    slow_mi4_v010(s, A, B, rows, cols);
    fast_mi4_v010(f, A, B, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-4) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(A); free(B); free(s); free(f);
    return pass ? 0 : 1;
}
