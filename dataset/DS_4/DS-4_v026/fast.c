#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v026(double *depth, double *x, double *y, double *g, int n) {
    double total_depth = 0.0;
    double total_x = 0.0;
    double total_y = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += depth[i];
        total_x += x[i];
        total_y += y[i];
        total_g += g[i];
    }
    return total_depth + total_x + total_y + total_g;
}