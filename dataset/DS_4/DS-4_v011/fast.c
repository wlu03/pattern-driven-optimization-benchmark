#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v011(double *vx, double *x, double *vy, double *y, int n) {
    double total_vx = 0.0;
    double total_x = 0.0;
    double total_vy = 0.0;
    double total_y = 0.0;
    int i = 0;
    while (i < n) {
        total_vx += vx[i];
        total_x += x[i];
        total_vy += vy[i];
        total_y += y[i];
        i++;
    }
    return total_vx + total_x + total_vy + total_y;
}