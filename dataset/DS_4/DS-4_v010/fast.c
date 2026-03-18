#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v010(double *v, double *pad2, int n) {
    double total_v = -1e308;
    double total_pad2 = -1e308;
    for (int i = 0; i < n; i++) {
        if (v[i] > total_v) total_v = v[i];
        if (pad2[i] > total_pad2) total_pad2 = pad2[i];
    }
    return total_v + total_pad2;
}