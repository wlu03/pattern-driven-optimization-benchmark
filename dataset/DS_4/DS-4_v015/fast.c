#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v015(double *g, int n) {
    double total_g = 1e308;
    int i = 0;
    while (i < n) {
        if (g[i] < total_g) total_g = g[i];
        i++;
    }
    return total_g;
}