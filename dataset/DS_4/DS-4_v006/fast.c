#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v006(double *py, double *nx, double *pz, int n) {
    double total_py = 0.0;
    double total_nx = 0.0;
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_py += py[i];
        total_nx += nx[i];
        total_pz += pz[i];
    }
    return total_py + total_nx + total_pz;
}