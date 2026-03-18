#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
    float phase;
} AoS_v021;

double slow_ds4_v021(AoS_v021 *arr, int n) {
    double total_amplitude = 1e308;
    double total_time = 1e308;
    double total_energy = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].amplitude < total_amplitude) total_amplitude = (double)arr[i].amplitude;
        if ((double)arr[i].time < total_time) total_time = (double)arr[i].time;
        if ((double)arr[i].energy < total_energy) total_energy = (double)arr[i].energy;
    }
    return total_amplitude + total_time + total_energy;
}