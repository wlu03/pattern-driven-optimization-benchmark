#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v005(double *g, double *r, double *b, double *a, int n) {
    double total_g = 0.0;
    double total_r = 0.0;
    double total_b = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_g += g[i];
        total_r += r[i];
        total_b += b[i];
        total_a += a[i];
    }
    return total_g + total_r + total_b + total_a;
}