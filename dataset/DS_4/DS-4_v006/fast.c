#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v006(double *energy, double *amplitude, int n) {
    double total_energy = 1e308;
    double total_amplitude = 1e308;
    int i = 0;
    while (i < n) {
        if (energy[i] < total_energy) total_energy = energy[i];
        if (amplitude[i] < total_amplitude) total_amplitude = amplitude[i];
        i++;
    }
    return total_energy + total_amplitude;
}