#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v011(double *ny, double *pad5, int n) {
    double total_ny = 0.0;
    double total_pad5 = 0.0;
    int i = 0;
    while (i < n) {
        total_ny += ny[i];
        total_pad5 += pad5[i];
        i++;
    }
    return total_ny + total_pad5;
}