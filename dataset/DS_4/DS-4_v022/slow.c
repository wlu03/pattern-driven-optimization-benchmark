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
} AoS_v022;

double slow_ds4_v022(AoS_v022 *arr, int n) {
    double total_u = 0.0;
    double total_v = 0.0;
    double total_px = 0.0;
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_u += (double)arr[i].u;
        total_v += (double)arr[i].v;
        total_px += (double)arr[i].px;
        total_pz += (double)arr[i].pz;
    }
    return total_u + total_v + total_px + total_pz;
}