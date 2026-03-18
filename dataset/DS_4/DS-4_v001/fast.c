#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v001(double *time, double *amplitude, double *y, int n) {
    double total_time = 0.0;
    double total_amplitude = 0.0;
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_time += time[i];
        total_amplitude += amplitude[i];
        total_y += y[i];
    }
    return total_time + total_amplitude + total_y;
}