#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v009(double *v, double *pz, double *u, double *ny, int n) {
    double total_v = 0.0;
    double total_pz = 0.0;
    double total_u = 0.0;
    double total_ny = 0.0;
    int i = 0;
    while (i < n) {
        total_v += v[i];
        total_pz += pz[i];
        total_u += u[i];
        total_ny += ny[i];
        i++;
    }
    return total_v + total_pz + total_u + total_ny;
}