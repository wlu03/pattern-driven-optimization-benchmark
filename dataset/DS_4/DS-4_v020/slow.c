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
} AoS_v020;

double slow_ds4_v020(AoS_v020 *arr, int n) {
    double total_x = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
        i++;
    }
    return total_x;
}