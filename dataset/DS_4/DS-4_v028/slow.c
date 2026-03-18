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
} AoS_v028;

double slow_ds4_v028(AoS_v028 *arr, int n) {
    double total_vz = 0.0;
    for (int i = 0; i < n; i++) {
        total_vz += (double)arr[i].vz;
    }
    return total_vz;
}