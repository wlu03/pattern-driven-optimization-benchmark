#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v025(double *z, double *vy, double *vz, int n) {
    double total_z = 0.0;
    double total_vy = 0.0;
    double total_vz = 0.0;
    int i = 0;
    while (i < n) {
        total_z += z[i];
        total_vy += vy[i];
        total_vz += vz[i];
        i++;
    }
    return total_z + total_vy + total_vz;
}