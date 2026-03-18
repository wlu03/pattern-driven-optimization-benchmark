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
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_u = 0.0;
    for (int i = 0; i < n; i++) {
        total_u += (double)arr[i].u;
    }
    return total_u;
}