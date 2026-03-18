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
} AoS_v012;

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_x = 0.0;
    double total_quality = 0.0;
    double total_channel = 0.0;
    for (int i = 0; i < n; i++) {
        total_x += (double)arr[i].x;
        total_quality += (double)arr[i].quality;
        total_channel += (double)arr[i].channel;
    }
    return total_x + total_quality + total_channel;
}