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
} AoS_v025;

double slow_ds4_v025(AoS_v025 *arr, int n) {
    double total_y = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
    }
    return total_y;
}