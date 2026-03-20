#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_mi4_v013(float *dst, float *src, int rows, int cols);
void fast_mi4_v013(float *dst, float *src, int rows, int cols);
int main() {
    int rows = 2000, cols = 4000, total = rows * cols;
    float *src = malloc(total * sizeof(float));
    float *s = malloc(total * sizeof(float));
    float *f = malloc(total * sizeof(float));
    for (int k = 0; k < total; k++) src[k] = (float)(k % 100) * 0.1;
    slow_mi4_v013(s, src, rows, cols);
    fast_mi4_v013(f, src, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-9) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(src); free(s); free(f);
    return pass ? 0 : 1;
}
