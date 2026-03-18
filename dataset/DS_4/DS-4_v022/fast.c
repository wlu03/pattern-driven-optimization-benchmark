#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v022(double *u, double *v, double *px, double *pz, int n) {
    double total_u = 0.0;
    double total_v = 0.0;
    double total_px = 0.0;
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_u += u[i];
        total_v += v[i];
        total_px += px[i];
        total_pz += pz[i];
    }
    return total_u + total_v + total_px + total_pz;
}