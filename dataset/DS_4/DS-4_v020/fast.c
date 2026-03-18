#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v020(double *u, double *nz, double *pz, int n) {
    double total_u = -1e308;
    double total_nz = -1e308;
    double total_pz = -1e308;
    int i = 0;
    while (i < n) {
        if (u[i] > total_u) total_u = u[i];
        if (nz[i] > total_nz) total_nz = nz[i];
        if (pz[i] > total_pz) total_pz = pz[i];
        i++;
    }
    return total_u + total_nz + total_pz;
}