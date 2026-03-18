#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v014(double *quality, double *y, double *energy, int n) {
    double total_quality = 1e308;
    double total_y = 1e308;
    double total_energy = 1e308;
    int i = 0;
    while (i < n) {
        if (quality[i] < total_quality) total_quality = quality[i];
        if (y[i] < total_y) total_y = y[i];
        if (energy[i] < total_energy) total_energy = energy[i];
        i++;
    }
    return total_quality + total_y + total_energy;
}