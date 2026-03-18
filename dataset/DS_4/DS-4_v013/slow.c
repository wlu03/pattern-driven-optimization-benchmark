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
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_pad6 = 0.0;
    double total_pad5 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad6 += (double)arr[i].pad6;
        total_pad5 += (double)arr[i].pad5;
    }
    return total_pad6 + total_pad5;
}