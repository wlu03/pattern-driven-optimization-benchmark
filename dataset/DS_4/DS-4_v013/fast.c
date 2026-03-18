#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v013(double *u, int n) {
    double total_u = 0.0;
    for (int i = 0; i < n; i++) {
        total_u += u[i];
    }
    return total_u;
}