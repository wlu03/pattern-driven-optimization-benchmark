#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v029(double *pz, int n) {
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if (pz[i] > total_pz) total_pz = pz[i];
    }
    return total_pz;
}