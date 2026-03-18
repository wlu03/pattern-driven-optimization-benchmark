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
    double total_v = 0.0;
    double total_pz = 0.0;
    double total_u = 0.0;
    double total_ny = 0.0;
    int i = 0;
    while (i < n) {
        total_v += (double)arr[i].v;
        total_pz += (double)arr[i].pz;
        total_u += (double)arr[i].u;
        total_ny += (double)arr[i].ny;
        i++;
    }
    return total_v + total_pz + total_u + total_ny;
}