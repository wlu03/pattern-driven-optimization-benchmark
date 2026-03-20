#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
void slow_mi4_v014(float *matrix, int rows, int cols);
void fast_mi4_v014(float *matrix, int rows, int cols);
int main() {
    int rows = 4000, cols = 1000;
    float *slow = malloc(rows * cols * sizeof(float));
    float *fast = malloc(rows * cols * sizeof(float));
    for (int k = 0; k < rows * cols; k++) slow[k] = (float)((k % 100) + 1) * 0.01;
    memcpy(fast, slow, rows * cols * sizeof(float));
    slow_mi4_v014(slow, rows, cols);
    fast_mi4_v014(fast, rows, cols);
    int pass = 1;
    for (int k = 0; k < rows * cols; k++) {
        if (fabs((double)(slow[k] - fast[k])) > 1e-6) { pass = 0; break; }
    }
    printf("%s\n", pass ? "PASS" : "FAIL");
    free(slow); free(fast);
    return pass ? 0 : 1;
}
