#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v012(double *normal_x, double *depth, double *g, double *a, int n) {
    double total_normal_x = 0.0;
    double total_depth = 0.0;
    double total_g = 0.0;
    double total_a = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_x += normal_x[i];
        total_depth += depth[i];
        total_g += g[i];
        total_a += a[i];
        i++;
    }
    return total_normal_x + total_depth + total_g + total_a;
}