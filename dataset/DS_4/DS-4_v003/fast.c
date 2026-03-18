#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v003(double *vz, int n) {
    double total_vz = -1e308;
    for (int i = 0; i < n; i++) {
        if (vz[i] > total_vz) total_vz = vz[i];
    }
    return total_vz;
}