#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v021(double *amplitude, double *time, double *energy, int n) {
    double total_amplitude = 1e308;
    double total_time = 1e308;
    double total_energy = 1e308;
    for (int i = 0; i < n; i++) {
        if (amplitude[i] < total_amplitude) total_amplitude = amplitude[i];
        if (time[i] < total_time) total_time = time[i];
        if (energy[i] < total_energy) total_energy = energy[i];
    }
    return total_amplitude + total_time + total_energy;
}