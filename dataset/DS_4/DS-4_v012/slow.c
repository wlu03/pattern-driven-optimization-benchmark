#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double time;
    double x;
    double y;
    double energy;
    double channel;
    double quality;
    double amplitude;
    double phase;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v012;

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].amplitude < total_amplitude) total_amplitude = (double)arr[i].amplitude;
    }
    return total_amplitude;
}