#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v007(double *g, int n) {
    double total_g = 1e308;
    for (int i = 0; i < n; i++) {
        if (g[i] < total_g) total_g = g[i];
    }
    return total_g;
}