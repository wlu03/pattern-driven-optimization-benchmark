#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v004(double *r, double *a, int n) {
    double total_r = 0.0;
    double total_a = 0.0;
    int i = 0;
    while (i < n) {
        total_r += r[i];
        total_a += a[i];
        i++;
    }
    return total_r + total_a;
}