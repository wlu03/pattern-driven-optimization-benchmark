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
} AoS_v028;

double slow_ds4_v028(AoS_v028 *arr, int n) {
    double total_py = -1e308;
    double total_nx = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].py > total_py) total_py = (double)arr[i].py;
        if ((double)arr[i].nx > total_nx) total_nx = (double)arr[i].nx;
    }
    return total_py + total_nx;
}