#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_mi4_v005(int *out, int *A, int *B, int rows, int cols);
void fast_mi4_v005(int *out, int *A, int *B, int rows, int cols);
int main() {
    int rows = 5000, cols = 5000, total = rows * cols;
    int *A = malloc(total * sizeof(int));
    int *B = malloc(total * sizeof(int));
    int *s = malloc(total * sizeof(int));
    int *f = malloc(total * sizeof(int));
    for (int k = 0; k < total; k++) { A[k] = (int)(k % 100) * 0.1; B[k] = (int)(k % 50) * 0.2; }
    slow_mi4_v005(s, A, B, rows, cols);
    fast_mi4_v005(f, A, B, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-4) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(A); free(B); free(s); free(f);
    return pass ? 0 : 1;
}
