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
} AoS_v024;

double slow_ds4_v024(AoS_v024 *arr, int n) {
    double total_amplitude = 0.0;
    double total_phase = 0.0;
    double total_y = 0.0;
    int i = 0;
    while (i < n) {
        total_amplitude += (double)arr[i].amplitude;
        total_phase += (double)arr[i].phase;
        total_y += (double)arr[i].y;
        i++;
    }
    return total_amplitude + total_phase + total_y;
}