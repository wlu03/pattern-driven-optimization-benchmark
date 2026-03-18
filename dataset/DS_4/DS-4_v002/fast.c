#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v002(double *ny, double *nx, double *px, int n) {
    double total_ny = 0.0;
    double total_nx = 0.0;
    double total_px = 0.0;
    int i = 0;
    while (i < n) {
        total_ny += ny[i];
        total_nx += nx[i];
        total_px += px[i];
        i++;
    }
    return total_ny + total_nx + total_px;
}