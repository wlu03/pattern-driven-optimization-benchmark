#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v012(double *amplitude, int n) {
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if (amplitude[i] < total_amplitude) total_amplitude = amplitude[i];
    }
    return total_amplitude;
}