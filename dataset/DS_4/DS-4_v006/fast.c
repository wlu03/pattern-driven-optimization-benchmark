#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v006(double *vx, double *z, double *mass, int n) {
    double total_vx = 0.0;
    double total_z = 0.0;
    double total_mass = 0.0;
    int i = 0;
    while (i < n) {
        total_vx += vx[i];
        total_z += z[i];
        total_mass += mass[i];
        i++;
    }
    return total_vx + total_z + total_mass;
}