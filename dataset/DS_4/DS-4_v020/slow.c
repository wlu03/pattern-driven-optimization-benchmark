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
} AoS_v020;

double slow_ds4_v020(AoS_v020 *arr, int n) {
    double total_u = -1e308;
    double total_nz = -1e308;
    double total_pz = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].u > total_u) total_u = (double)arr[i].u;
        if ((double)arr[i].nz > total_nz) total_nz = (double)arr[i].nz;
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
        i++;
    }
    return total_u + total_nz + total_pz;
}