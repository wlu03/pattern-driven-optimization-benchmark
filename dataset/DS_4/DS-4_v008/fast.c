#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v008(double *depth, double *r, double *g, double *b, int n) {
    double total_depth = 0.0;
    double total_r = 0.0;
    double total_g = 0.0;
    double total_b = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += depth[i];
        total_r += r[i];
        total_g += g[i];
        total_b += b[i];
    }
    return total_depth + total_r + total_g + total_b;
}