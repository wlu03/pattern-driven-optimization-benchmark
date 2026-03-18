#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v003(double *pressure, int n) {
    double total_pressure = 0.0;
    int i = 0;
    while (i < n) {
        total_pressure += pressure[i];
        i++;
    }
    return total_pressure;
}