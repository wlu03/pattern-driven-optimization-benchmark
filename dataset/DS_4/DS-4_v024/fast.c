#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v024(double *amplitude, double *phase, double *y, int n) {
    double total_amplitude = 0.0;
    double total_phase = 0.0;
    double total_y = 0.0;
    int i = 0;
    while (i < n) {
        total_amplitude += amplitude[i];
        total_phase += phase[i];
        total_y += y[i];
        i++;
    }
    return total_amplitude + total_phase + total_y;
}