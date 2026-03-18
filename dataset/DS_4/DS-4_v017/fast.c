#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v017(double *vx, double *charge, double *vz, int n) {
    double total_vx = 0.0;
    double total_charge = 0.0;
    double total_vz = 0.0;
    for (int i = 0; i < n; i++) {
        total_vx += vx[i];
        total_charge += charge[i];
        total_vz += vz[i];
    }
    return total_vx + total_charge + total_vz;
}