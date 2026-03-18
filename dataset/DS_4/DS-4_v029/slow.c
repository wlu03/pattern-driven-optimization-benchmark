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
} AoS_v029;

double slow_ds4_v029(AoS_v029 *arr, int n) {
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
    }
    return total_pz;
}