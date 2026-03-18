#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v016(double *b, double *x, int n) {
    double total_b = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if (b[i] < total_b) total_b = b[i];
        if (x[i] < total_x) total_x = x[i];
    }
    return total_b + total_x;
}