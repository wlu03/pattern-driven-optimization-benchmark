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
} AoS_v015;

double slow_ds4_v015(AoS_v015 *arr, int n) {
    double total_pad4 = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].pad4 > total_pad4) total_pad4 = (double)arr[i].pad4;
        i++;
    }
    return total_pad4;
}