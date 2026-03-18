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
} AoS_v006;

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_py = 0.0;
    double total_nx = 0.0;
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_py += (double)arr[i].py;
        total_nx += (double)arr[i].nx;
        total_pz += (double)arr[i].pz;
    }
    return total_py + total_nx + total_pz;
}