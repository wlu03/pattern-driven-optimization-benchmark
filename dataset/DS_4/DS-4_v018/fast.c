#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v018(double *nz, int n) {
    double total_nz = 0.0;
    for (int i = 0; i < n; i++) {
        total_nz += nz[i];
    }
    return total_nz;
}