#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v019(double *r, double *x, double *normal_x, double *a, int n) {
    double total_r = 0.0;
    double total_x = 0.0;
    double total_normal_x = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_r += r[i];
        total_x += x[i];
        total_normal_x += normal_x[i];
        total_a += a[i];
    }
    return total_r + total_x + total_normal_x + total_a;
}