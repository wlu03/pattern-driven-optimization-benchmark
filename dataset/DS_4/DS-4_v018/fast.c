#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v018(double *r, double *depth, double *normal_x, double *a, int n) {
    double total_r = -1e308;
    double total_depth = -1e308;
    double total_normal_x = -1e308;
    double total_a = -1e308;
    for (int i = 0; i < n; i++) {
        if (r[i] > total_r) total_r = r[i];
        if (depth[i] > total_depth) total_depth = depth[i];
        if (normal_x[i] > total_normal_x) total_normal_x = normal_x[i];
        if (a[i] > total_a) total_a = a[i];
    }
    return total_r + total_depth + total_normal_x + total_a;
}