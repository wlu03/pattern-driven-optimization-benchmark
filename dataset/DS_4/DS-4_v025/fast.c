#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v025(double *amplitude, int n) {
    double total_amplitude = 0.0;
    int i = 0;
    while (i < n) {
        total_amplitude += amplitude[i];
        i++;
    }
    return total_amplitude;
}