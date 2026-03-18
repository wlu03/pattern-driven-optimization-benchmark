#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v009(double *nz, double *v, double *px, double *ny, int n) {
    double total_nz = -1e308;
    double total_v = -1e308;
    double total_px = -1e308;
    double total_ny = -1e308;
    for (int i = 0; i < n; i++) {
        if (nz[i] > total_nz) total_nz = nz[i];
        if (v[i] > total_v) total_v = v[i];
        if (px[i] > total_px) total_px = px[i];
        if (ny[i] > total_ny) total_ny = ny[i];
    }
    return total_nz + total_v + total_px + total_ny;
}