#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v010(double *y, double *x, int n) {
    double total_y = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if (y[i] < total_y) total_y = y[i];
        if (x[i] < total_x) total_x = x[i];
    }
    return total_y + total_x;
}