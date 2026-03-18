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
} AoS_v014;

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_quality = 1e308;
    double total_y = 1e308;
    double total_energy = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].quality < total_quality) total_quality = (double)arr[i].quality;
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].energy < total_energy) total_energy = (double)arr[i].energy;
        i++;
    }
    return total_quality + total_y + total_energy;
}