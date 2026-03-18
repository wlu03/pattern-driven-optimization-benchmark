#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
} AoS_v003;

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_vz = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].vz > total_vz) total_vz = (double)arr[i].vz;
    }
    return total_vz;
}