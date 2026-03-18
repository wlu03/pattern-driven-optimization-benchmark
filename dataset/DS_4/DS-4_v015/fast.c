#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v015(double *x, int n) {
    double total_x = 1e308;
    int i = 0;
    while (i < n) {
        if (x[i] < total_x) total_x = x[i];
        i++;
    }
    return total_x;
}