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
    float u;
    float v;
} AoS_v009;

double slow_ds4_v009(AoS_v009 *arr, int n) {
    double total_nz = -1e308;
    double total_v = -1e308;
    double total_px = -1e308;
    double total_ny = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].nz > total_nz) total_nz = (double)arr[i].nz;
        if ((double)arr[i].v > total_v) total_v = (double)arr[i].v;
        if ((double)arr[i].px > total_px) total_px = (double)arr[i].px;
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
    }
    return total_nz + total_v + total_px + total_ny;
}