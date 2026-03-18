#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v002;

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_ny = 0.0;
    double total_nx = 0.0;
    double total_px = 0.0;
    int i = 0;
    while (i < n) {
        total_ny += (double)arr[i].ny;
        total_nx += (double)arr[i].nx;
        total_px += (double)arr[i].px;
        i++;
    }
    return total_ny + total_nx + total_px;
}