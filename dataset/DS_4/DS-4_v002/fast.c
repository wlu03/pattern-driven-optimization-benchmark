#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v002(double *depth, double *y, double *b, double *normal_x, int n) {
    double total_depth = 0.0;
    double total_y = 0.0;
    double total_b = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_depth += depth[i];
        total_y += y[i];
        total_b += b[i];
        total_normal_x += normal_x[i];
        i++;
    }
    return total_depth + total_y + total_b + total_normal_x;
}