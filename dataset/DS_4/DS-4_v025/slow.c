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
} AoS_v025;

double slow_ds4_v025(AoS_v025 *arr, int n) {
    double total_amplitude = 0.0;
    int i = 0;
    while (i < n) {
        total_amplitude += (double)arr[i].amplitude;
        i++;
    }
    return total_amplitude;
}