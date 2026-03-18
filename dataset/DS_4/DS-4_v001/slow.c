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
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_time = 0.0;
    double total_amplitude = 0.0;
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_time += (double)arr[i].time;
        total_amplitude += (double)arr[i].amplitude;
        total_y += (double)arr[i].y;
    }
    return total_time + total_amplitude + total_y;
}