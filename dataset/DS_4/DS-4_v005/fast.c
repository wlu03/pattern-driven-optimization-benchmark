#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v005(double *y, double *depth, double *a, int n) {
    double total_y = 0.0;
    double total_depth = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += y[i];
        total_depth += depth[i];
        total_a += a[i];
    }
    return total_y + total_depth + total_a;
}